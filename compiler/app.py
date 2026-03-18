from flask import Flask, render_template, request, jsonify
# Import your logic from lexer.py
from lexer import Lexer, Parser, CodeGenerator

app = Flask(__name__)

def translate_c_to_python(c_code):
    try:
        # Initializing your transpiler pipeline
        lexer = Lexer(c_code)
        tokens = lexer.tokenize()
        
        parser = Parser(tokens)
        ast = parser.parse()
        
        generator = CodeGenerator()
        return generator.generate(ast)
    except Exception as e:
        return f"Error during translation: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/translate', methods=['POST'])
def translate():
    data = request.json
    c_code = data.get("code", "")
    python_code = translate_c_to_python(c_code)
    return jsonify({"python_code": python_code})

if __name__ == '__main__':
    # debug=True allows the server to auto-reload when you make changes
    app.run(debug=True)