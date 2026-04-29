from flask import Flask, render_template, request, jsonify

from lexer import Lexer, Parser, CodeGenerator
from semantic import SemanticAnalyzer
from optimizer import Optimizer

app = Flask(__name__)


def translate_c_to_python(c_code):
    try:
        lexer = Lexer(c_code)
        tokens = lexer.tokenize()

        parser = Parser(tokens)
        ast = parser.parse()

        semantic = SemanticAnalyzer()
        semantic.visit(ast)
        # Optionally log warnings: semantic.warnings

        optimizer = Optimizer()
        ast = optimizer.optimize(ast)

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
    print("Starting Flask server...")
    app.run(debug=True)