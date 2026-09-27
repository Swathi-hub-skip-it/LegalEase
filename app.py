from flask import Flask, render_template, request, send_file
from google import genai
from dotenv import load_dotenv
import os
import markdown
from io import BytesIO
from docx import Document
from fpdf import FPDF

load_dotenv()

app = Flask(__name__)
documents = []
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is missing in .env file")

client = genai.Client(api_key=api_key)
@app.route("/download/txt", methods=["POST"])
def download_txt():
    content = request.form.get("content", "")

    file = BytesIO()
    file.write(content.encode("utf-8"))
    file.seek(0)

    return send_file(
        file,
        as_attachment=True,
        download_name="LegalEase_Document.txt",
        mimetype="text/plain"
    )


@app.route("/download/docx", methods=["POST"])
def download_docx():
    content = request.form.get("content", "")

    document = Document()
    document.add_heading("LegalEase Legal Document", 0)

    for line in content.splitlines():
        if line.strip():
            document.add_paragraph(line)

    file = BytesIO()
    document.save(file)
    file.seek(0)

    return send_file(
        file,
        as_attachment=True,
        download_name="LegalEase_Document.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


@app.route("/download/pdf", methods=["POST"])
def download_pdf():
    content = request.form.get("content", "")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for line in content.splitlines():
        if line.strip():
            pdf.multi_cell(0, 8, line)

    pdf_bytes = bytes(pdf.output())

    file = BytesIO(pdf_bytes)

    return send_file(
        file,
        as_attachment=True,
        download_name="LegalEase_Document.pdf",
        mimetype="application/pdf"
    )
@app.route("/history")
def history():
    return render_template("history.html", documents=documents)

@app.route("/", methods=["GET", "POST"])
def home():
    result = ""

    if request.method == "POST":
        document_type = request.form.get("document_type")
        details = request.form.get("details")

        prompt = f"""
You are LegalEase, an AI-powered legal document drafting assistant.

Create a clear and professional draft for the following document.

Document Type:
{document_type}

User Details:
{details}

Requirements:
- Use clear and formal language.
- Organize the document with suitable headings.
- Include relevant clauses based on the information provided.
- Do not present the output as legal advice.
- Add a short note that the generated document should be reviewed
  by a qualified legal professional before use.
- Use simple Markdown formatting only.
- Use # for main headings and ## for section headings.
- Use **bold** only when necessary.
- Do not use triple asterisks (***).
- Do not use unnecessary underscores or decorative symbols.
- Keep the document clean and professional.
"""

        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )

            result = markdown.markdown(
                response.text,
                extensions=["extra"]
            )
            documents.append({
                "document_type": document_type,
                "details": details,
                "content": result
            })

        except Exception as e:
            error_message = str(e)
            if "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:
                result = """
                <div class="error-message">
                    <h3>⚠️ AI Request Limit Reached</h3>
                    <p>The Gemini free-tier request limit has been reached.</p>
                    <p>Please wait for the quota to reset and try again later.</p>
                </div>
                """

            elif "503" in error_message or "UNAVAILABLE" in error_message:
                result = """
                <div class="error-message">
                    <h3>⚠️ Gemini AI is temporarily busy</h3>
                    <p>The AI service is currently experiencing high demand.</p>
                    <p>Please wait a few seconds and try again.</p>
                </div>
                """
            else:
                result = f"""
                <div class="error-message">
                    <h3>⚠️ Something went wrong</h3>
                    <p>{error_message}</p>
                </div>
                """

    return render_template("index.html", result=result)


if __name__ == "__main__":
    app.run(debug=True)