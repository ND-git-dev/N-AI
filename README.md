# N-AI — Universal Termux LLM Launcher

**N-AI** is a lightweight, zero-configuration launcher designed to run local Large Language Models (LLMs) on Android via Termux. It handles dependency installation, compiles `llama.cpp` specifically for your phone's processor, and monitors hardware limits for maximum performance.

---

## Key Features

* **Global System Command**: Run `nai` from any folder or path in Termux after the first run.
* **Zero-Config Installer**: Auto-installs Python, C++ build tools, and compiles `llama-cli` and `llama-server` on setup.
* **Dual Execution Modes**:
  * **Terminal Chat**: Low-RAM interactive console session.
  * **Local Web Server**: Starts an API/Web server at `http://127.0.0.1:8080`.
* **Hardware Safeguards**: Checks free RAM and disk storage before loading models to prevent system crashes.
* **Smart Model Discovery**: Automatically scans device storage for `.gguf` files while ignoring non-model vocabulary files.
* **Zero RAM Overhead**: Python hands off process control directly to C++ binaries (`os.execvp`), freeing memory for model inference.

---

## Quick Installation

Open Termux and run the following commands:

```bash
termux-setup-storage
pkg install git -y
git clone [https://github.com/ND-git-dev/N-AI.git](https://github.com/ND-git-dev/N-AI.git)
cd N-AI && chmod +x nai && ./nai
