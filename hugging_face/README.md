# Hugging Face 图片物体识别 Demo

使用本地图片路径作为输入，基于 `facebook/detr-resnet-50`（COCO 通用检测）识别常见物体，并在图上绘制边框与类别标签（含置信度）。

## 环境要求

- Python 3.10+（建议）
- 已安装 [PyTorch](https://pytorch.org/)（`requirements.txt` 中的 `torch`；若需 GPU 请按官网选择对应 CUDA 版本）

## 快速开始

```bash
cd hugging_face
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
# source .venv/bin/activate

pip install -r requirements.txt
pip install jupyter
jupyter notebook hf_object_detection_demo.ipynb
```

在 notebook 中按顺序运行单元格，并在「可调参数」处设置：

- `image_path`：你的本地图片路径
- `score_threshold`：置信度阈值（默认约 `0.6`）
- `save_output` / 输出路径：是否保存标注图（如 `output_annotated.jpg`）

### 国内网络与 Hugging Face Hub

若下载模型较慢或超时，可在**第一个代码单元**（导入 `transformers` 之前）设置镜像，例如：

```python
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "600")
```

notebook 内已包含类似说明与常见报错提示。

## 仓库文件说明

| 文件 | 说明 |
|------|------|
| `hf_object_detection_demo.ipynb` | 主流程：检测、过滤、绘制与展示 |
| `requirements.txt` | Python 依赖 |
| `app.py` / `ms_deploy.json` | （可选）ModelScope 创空间部署用 Gradio 应用 |

## 许可证与模型

- 代码以你仓库根目录的许可证为准。
- 预训练模型版权归 Meta / Hugging Face 及相应许可条款约束，请遵守 [facebook/detr-resnet-50](https://huggingface.co/facebook/detr-resnet-50) 页面说明。
