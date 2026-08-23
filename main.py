import os
import sys
import glob
import json
import shutil
import subprocess

CONFIG_FILE = os.path.expanduser("~/.nai_config.json")
SUPPORTED_EXTENSIONS = [".gguf", ".onnx", ".safetensors"]

def get_free_ram_mb():
    try:
        with open("/proc/meminfo", "r") as f:
            lines = f.readlines()
        mem = {}
        for line in lines:
            parts = line.split(":")
            if len(parts) == 2:
                mem[parts[0].strip()] = int(parts[1].split()[0])
        avail_kb = mem.get("MemAvailable", mem.get("MemFree", 0))
        return avail_kb // 1024
    except Exception:
        return 2048

def get_free_storage_gb(path="~"):
    total, used, free = shutil.disk_usage(os.path.expanduser(path))
    return free / (1024 ** 3)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
    except Exception:
        pass

def ensure_llama_cpp():
    cli_path = shutil.which("llama-cli") or os.path.expanduser("~/bin/llama-cli")
    server_path = shutil.which("llama-server") or os.path.expanduser("~/bin/llama-server")

    if os.path.exists(cli_path) and os.path.exists(server_path):
        return cli_path, server_path

    print("\n[NAI] Compiling llama.cpp binaries locally (one-time process)...")
    os.makedirs(os.path.expanduser("~/bin"), exist_ok=True)
    subprocess.run("pkg install -y cmake clang git build-essential", shell=True, check=True)
    
    tmp_dir = os.path.expanduser("~/tmpllama")
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
        
    subprocess.run(f"git clone https://github.com/ggerganov/llama.cpp.git {tmp_dir}", shell=True, check=True)
    subprocess.run(f"cd {tmp_dir} && cmake -B build && cmake --build build --config Release -j$(nproc)", shell=True, check=True)
    
    shutil.move(os.path.join(tmp_dir, "build/bin/llama-cli"), os.path.expanduser("~/bin/llama-cli"))
    shutil.move(os.path.join(tmp_dir, "build/bin/llama-server"), os.path.expanduser("~/bin/llama-server"))
    shutil.rmtree(tmp_dir)
    return os.path.expanduser("~/bin/llama-cli"), os.path.expanduser("~/bin/llama-server")

def scan_models():
    search_paths = [os.path.expanduser("~/"), "/sdcard/Download/", "/sdcard/Documents/"]
    found = []
    for path in search_paths:
        if os.path.exists(path):
            for ext in SUPPORTED_EXTENSIONS:
                found.extend(glob.glob(os.path.join(path, f"**/*{ext}"), recursive=True))
    
    clean_models = []
    seen_real_paths = set()

    for m in found:
        if "ggml-vocab" in os.path.basename(m).lower():
            continue
        if os.path.getsize(m) < (50 * 1024 * 1024):
            continue

        real_p = os.path.realpath(m)
        if real_p not in seen_real_paths:
            seen_real_paths.add(real_p)
            clean_models.append(m)

    return clean_models

def handle_url_download():
    url = input("\nPaste Model Download URL: ").strip()
    if not url:
        return None

    dest_dir = os.path.expanduser("~/models")
    os.makedirs(dest_dir, exist_ok=True)
    filename = url.split("/")[-1].split("?")[0]
    output_path = os.path.join(dest_dir, filename)

    print(f"[NAI] Downloading model to {output_path}...")
    subprocess.run(["wget", "-O", output_path, url], check=True)
    return output_path

def main():
    print("==========================================")
    print("      NAI: Universal Termux Launcher      ")
    print("==========================================")
    
    config = load_config()
    avail_ram_mb = get_free_ram_mb()
    free_storage_gb = get_free_storage_gb()
    
    print(f"System Status: {avail_ram_mb} MB RAM Free | {free_storage_gb:.1f} GB Storage Free\n")

    models = scan_models()
    
    print("Available Options:")
    print(" [0] Download new model via URL")
    for i, m in enumerate(models):
        size_mb = os.path.getsize(m) / (1024 * 1024)
        print(f" [{i + 1}] {os.path.basename(m)} | {size_mb:.0f} MB")

    choice = input("\nSelect an option: ").strip()

    if choice == "0":
        selected_model = handle_url_download()
        if not selected_model:
            sys.exit(0)
    else:
        try:
            selected_model = models[int(choice) - 1]
        except (ValueError, IndexError):
            print("Invalid selection.")
            sys.exit(1)

    print("\nSelect Run Mode:")
    print(" [1] Terminal Chat Mode (llama-cli)")
    print(" [2] Local Web Server Mode (http://127.0.0.1:8080)")
    mode = input("Mode Choice (Default 1): ").strip() or "1"

    last_threads = config.get("threads", str(os.cpu_count()))
    last_ctx = config.get("ctx", "2048")

    threads = input(f"CPU Threads (Default {last_threads}): ").strip() or last_threads
    ctx = input(f"Context Window (Default {last_ctx}): ").strip() or last_ctx

    config["threads"] = threads
    config["ctx"] = ctx
    config["last_model"] = selected_model
    save_config(config)

    ext = os.path.splitext(selected_model)[1].lower()

    if ext == ".gguf":
        cli_bin, server_bin = ensure_llama_cpp()

        if mode == "2":
            args = [
                server_bin,
                "-m", selected_model,
                "-c", ctx,
                "-t", threads,
                "--host", "127.0.0.1",
                "--port", "8080"
            ]
            print("\n[NAI] Starting Web Server at http://127.0.0.1:8080 ...")
            os.execvp(server_bin, args)
        else:
            args = [
                cli_bin,
                "-m", selected_model,
                "-t", threads,
                "-c", ctx,
                "--color", "auto",
                "-cnv"
            ]
            print("\n[NAI] Starting Terminal Chat Mode...")
            os.execvp(cli_bin, args)

if __name__ == "__main__":
    main()
