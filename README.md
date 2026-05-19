# Dishonesty

Real browser AI for Chrome and Chromebooks.

## Use

1. Unzip `dishonesty-real-models.zip`.
2. Open `index.html` in Chrome.
3. Pick a model in Model Hub.

All listed models are real ONNX language models for Transformers.js/WebGPU:

- Qwen 2.5 0.5B
- Qwen 2.5 Coder 0.5B
- Gemma 3 1B IT

Each model needs internet the first time Chrome downloads it. After that, Chrome may reuse the browser cache on the same device.

## Runtime Controls

The Settings page includes temperature, max tokens, top-p, repeat penalty, sampling, device, quantization, and system prompt controls. Settings save in the browser automatically.

## Local Tools

Use `/math 2 + 2`, `/ascii hello`, or `/preview <h1>Hello</h1>` in chat. Model responses render Markdown, including code blocks and lists, and HTML previews open in a sandboxed iframe.
