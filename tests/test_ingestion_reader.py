import json
import shutil
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


langchain_module = types.ModuleType("langchain")
text_splitter_module = types.ModuleType("langchain.text_splitter")


class RecursiveCharacterTextSplitter:
    def __init__(self, chunk_size, chunk_overlap):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text):
        return [text] if text else []


text_splitter_module.RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter
langchain_module.text_splitter = text_splitter_module
sys.modules.setdefault("langchain", langchain_module)
sys.modules.setdefault("langchain.text_splitter", text_splitter_module)

community_module = types.ModuleType("langchain_community")
document_loaders_module = types.ModuleType("langchain_community.document_loaders")


class _LoaderStub:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def load(self):
        return []


document_loaders_module.PyPDFLoader = _LoaderStub
document_loaders_module.TextLoader = _LoaderStub
community_module.document_loaders = document_loaders_module
sys.modules.setdefault("langchain_community", community_module)
sys.modules.setdefault("langchain_community.document_loaders", document_loaders_module)

unstructured_module = types.ModuleType("unstructured")
partition_pkg = types.ModuleType("unstructured.partition")
partition_auto_module = types.ModuleType("unstructured.partition.auto")
partition_auto_module.partition = lambda filename: []
partition_pkg.auto = partition_auto_module
unstructured_module.partition = partition_pkg
sys.modules.setdefault("unstructured", unstructured_module)
sys.modules.setdefault("unstructured.partition", partition_pkg)
sys.modules.setdefault("unstructured.partition.auto", partition_auto_module)

from langchain_ai_agent.ingestion.reader import DocumentIngestor


class TestDocumentIngestorRouting(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("tests/tmp_reader")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.ingestor = DocumentIngestor()

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @patch("langchain_ai_agent.ingestion.reader.PyPDFLoader")
    def test_pdf_uses_pdf_loader(self, mock_pdf_loader):
        pdf_path = self.test_dir / "manual.pdf"
        pdf_path.write_bytes(b"%PDF-1.4")

        mock_pdf_loader.return_value.load.return_value = [
            MagicMock(page_content="page 1"),
            MagicMock(page_content="page 2"),
        ]

        text = self.ingestor._extract_text(pdf_path)

        self.assertEqual(text, "page 1\npage 2")
        mock_pdf_loader.assert_called_once_with(str(pdf_path))

    @patch("langchain_ai_agent.ingestion.reader.TextLoader")
    def test_txt_and_md_use_text_loader_with_utf8(self, mock_text_loader):
        txt_path = self.test_dir / "notes.txt"
        md_path = self.test_dir / "guide.md"
        txt_path.write_text("hello", encoding="utf-8")
        md_path.write_text("# heading", encoding="utf-8")

        mock_text_loader.return_value.load.side_effect = [
            [MagicMock(page_content="hello")],
            [MagicMock(page_content="# heading")],
        ]

        txt_text = self.ingestor._extract_text(txt_path)
        md_text = self.ingestor._extract_text(md_path)

        self.assertEqual(txt_text, "hello")
        self.assertEqual(md_text, "# heading")
        self.assertEqual(mock_text_loader.call_args_list[0].args, (str(txt_path),))
        self.assertEqual(mock_text_loader.call_args_list[0].kwargs, {"encoding": "utf-8"})
        self.assertEqual(mock_text_loader.call_args_list[1].args, (str(md_path),))
        self.assertEqual(mock_text_loader.call_args_list[1].kwargs, {"encoding": "utf-8"})

    def test_json_and_jsonl_use_utf8_sig(self):
        json_path = self.test_dir / "data.json"
        jsonl_path = self.test_dir / "data.jsonl"

        json_path.write_text(
            "\ufeff" + json.dumps({"title": "扫地机器人", "steps": ["开机", "建图"]}, ensure_ascii=False),
            encoding="utf-8",
        )
        jsonl_path.write_text(
            "\ufeff"
            + json.dumps({"page": 1, "text": "第一页"}, ensure_ascii=False)
            + "\n"
            + json.dumps({"page": 2, "text": "第二页"}, ensure_ascii=False)
            + "\n",
            encoding="utf-8",
        )

        json_text = self.ingestor._extract_text(json_path)
        jsonl_text = self.ingestor._extract_text(jsonl_path)

        self.assertIn("扫地机器人", json_text)
        self.assertIn("第一页", jsonl_text)
        self.assertIn("第二页", jsonl_text)
