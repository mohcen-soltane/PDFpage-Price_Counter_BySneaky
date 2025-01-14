import os
import glob
import fitz  # PyMuPDF
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

def is_page_live(page):
    """
    Check if a PDF page is "live" (contains selectable text).
    """
    text = page.get_text()
    return bool(text)  # Returns True if text is non-empty, otherwise False

def process_pdf_file(pdf_file, check_live_dead=True):
    """
    Process a single PDF file and count live/dead pages.
    """
    live_pages = 0
    dead_pages = 0

    doc = fitz.open(pdf_file)
    num_pages = doc.page_count

    # Check each page
    for page_num in range(num_pages):
        page = doc.load_page(page_num)
        if check_live_dead:
            if is_page_live(page):
                live_pages += 1
                print(f"Page {page_num + 1}: Live")
            else:
                dead_pages += 1
                print(f"Page {page_num + 1}: Dead")
        else:
            print(f"Page {page_num + 1}: Processed (Quick Mode)")
            live_pages += 1  # In quick mode, all pages are considered live

    return num_pages, live_pages, dead_pages

def count_pdf_pages(path, check_live_dead=True):
    """
    Count the total number of pages in the provided path (file or folder) and determine their status.
    """
    total_pages = 0
    live_pages = 0
    dead_pages = 0

    # Check if the path is a file or folder
    if os.path.isfile(path):
        # Process a single file
        if path.lower().endswith(".pdf"):
            num_pages, live, dead = process_pdf_file(path, check_live_dead)
            total_pages += num_pages
            live_pages += live
            dead_pages += dead
        else:
            return None, "The provided file is not a PDF."
    elif os.path.isdir(path):
        # Process all PDF files in the folder
        pdf_files = glob.glob(os.path.join(path, "*.pdf"))
        if not pdf_files:
            return None, "No PDF files found in the folder."

        for pdf_file in pdf_files:
            num_pages, live, dead = process_pdf_file(pdf_file, check_live_dead)
            total_pages += num_pages
            live_pages += live
            dead_pages += dead
    else:
        return None, "The provided path is neither a file nor a folder."

    # Determine the status
    if check_live_dead:
        if live_pages == total_pages:
            status = "live"
        elif dead_pages == total_pages:
            status = "dead"
        else:
            status = "partial live"
    else:
        status = "quick processed"

    # Calculate expected prices
    one_column_price = total_pages * 1.5
    two_column_price = total_pages * 2.0
    arabic_price = total_pages * 3.0

    # Prepare results
    results = {
        "total_pages": total_pages,
        "live_pages": live_pages,
        "dead_pages": dead_pages,
        "status": status,
        "one_column_price": f"{one_column_price:.2f}",
        "two_column_price": f"{two_column_price:.2f}",
        "arabic_price": f"{arabic_price:.2f}"
    }

    return results, None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process", methods=["POST"])
def process():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"})

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"})

    if file and file.filename.lower().endswith(".pdf"):
        # Save the file temporarily
        file_path = os.path.join("/tmp", file.filename)
        file.save(file_path)

        # Process the file
        results, error = count_pdf_pages(file_path)

        # Delete the temporary file
        os.remove(file_path)

        if error:
            return jsonify({"error": error})
        else:
            return jsonify(results)
    else:
        return jsonify({"error": "The provided file is not a PDF"})

@app.route("/process_manual", methods=["POST"])
def process_manual():
    try:
        total_pages = int(request.form.get("total_pages"))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid number of pages. Please enter a valid integer."})

    # Calculate expected prices
    one_column_price = total_pages * 1.5
    two_column_price = total_pages * 2.0
    arabic_price = total_pages * 3.0

    # Prepare results
    results = {
        "total_pages": total_pages,
        "one_column_price": f"{one_column_price:.2f}",
        "two_column_price": f"{two_column_price:.2f}",
        "arabic_price": f"{arabic_price:.2f}"
    }

    return jsonify(results)

@app.route("/shutdown", methods=["POST"])
def shutdown():
    """
    Shutdown the Flask app when the browser window is closed.
    """
    os._exit(0)  # Forcefully terminate the app
    return "Shutting down..."

if __name__ == "__main__":
    # Run the Flask app
    port = int(os.environ.get("PORT", 5000))  # Use Render's port or default to 5000
    app.run(host="0.0.0.0", port=port)
