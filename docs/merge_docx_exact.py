from copy import deepcopy
from pathlib import Path

from docx import Document


def append_document_exact(base_doc: Document, append_doc: Document) -> None:
    body = base_doc.element.body
    sect_pr = body.sectPr

    base_doc.add_page_break()

    for element in append_doc.element.body:
        if element.tag.endswith('sectPr'):
            continue
        body.insert(body.index(sect_pr), deepcopy(element))


def merge_docs(first_path: Path, second_path: Path, output_path: Path) -> None:
    first_doc = Document(str(first_path))
    second_doc = Document(str(second_path))

    append_document_exact(first_doc, second_doc)
    first_doc.save(str(output_path))


if __name__ == '__main__':
    docs_dir = Path(__file__).resolve().parent

    first = docs_dir / 'ms-auditoria_Documento_Consolidado.docx'
    second = docs_dir / 'ms-auditoria_Documento_Consolidado_v2.docx'
    output = docs_dir / 'ms-auditoria_Documento_Consolidado_UNICO.docx'

    if not first.exists():
        raise FileNotFoundError(f'No se encontró: {first}')
    if not second.exists():
        raise FileNotFoundError(f'No se encontró: {second}')

    merge_docs(first, second, output)
    print(f'✅ Documento único generado: {output}')
