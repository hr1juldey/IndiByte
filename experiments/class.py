import dspy
import base64

llm = dspy.LM(
            model="ollama/qwen3-vl:8b",
            api_base="http://localhost:11434",
            api_key=""
        )
dspy.configure(lm=llm)

dspy.configure_cache(enable_disk_cache=False, enable_memory_cache=False)


def encode_image_to_base64(image_path: str) -> str:
    """Convert an image file to a base64-encoded string."""
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return encoded_string

class Scanner(dspy.Signature):
    """Perform exact structured OCR of the image and return ALL details unchanged return in markdown format"""
    image_1: dspy.Image = dspy.InputField(desc="A product package image that might contain food package label and food data")
    answer: str = dspy.OutputField(desc="markdown formatted ocr data in the same layout as image")
    
class Formatter(dspy.Signature):
    """Format raw text into clean, structured Markdown."""

    raw_text: str = dspy.InputField(
        desc="The unprocessed or messy text to be cleaned and formatted."
    )

    clean_md: str = dspy.OutputField(
        desc="Well-formatted Markdown output."
    )

image_url = "/home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense/data/food_labels/test_ocr.jpeg"
classify = dspy.ChainOfThought(Scanner)
result = classify(image_1=dspy.Image(image_url, download = True))
# print("Result object:", result)
# print("Answer field:", result.answer)
print("\n" + "="*80)
print("OCR DATA:")
print(result.answer)
print("="*80)
print("\nHistory:")
print(dspy.inspect_history(n = 1))