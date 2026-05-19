# 方式 A：Windows 本机安装 MeloTTS（Python 3.12 友好）
# - fugashi>=1.5.2 使用预编译 wheel（无需 MSVC）
# - transformers/tokenizers 使用 Py3.12 有 wheel 的版本（无需 Rust）

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Write-Host "==> 1/4 安装依赖（PyTorch 等，约 5–15 分钟）..."
pip install -r scripts/requirements-melotts-win.txt

Write-Host "==> 2/4 安装 MeloTTS（--no-deps，避免覆盖 tokenizers）..."
pip install "git+https://github.com/myshell-ai/MeloTTS.git" --no-deps

Write-Host "==> 3/4 安装/更新 tts-atom..."
pip install -e ".[dev]"

Write-Host "==> 4/5 下载 NLTK 数据（中英混合文本需要）..."
python -c "import nltk; nltk.download('averaged_perceptron_tagger'); nltk.download('averaged_perceptron_tagger_eng')"

Write-Host "==> 5/5 验证..."
python -c "from tts_atom.providers.melotts_runtime import detect_backend; print('backend', detect_backend())"
tts-atom doctor --json

Write-Host ""
Write-Host "首次合成会下载 HuggingFace 模型到 models/，请保持网络畅通。"
Write-Host '  tts-atom synth --text "你好，小警员" --provider melotts --json'
