from flask import Flask, render_template, request, jsonify
from lexer import Lexer, Parser, CodeGenerator
from semantic import SemanticAnalyzer, SemanticAnalysisError

app = Flask(__name__)

def translate_c_to_python(c_code):
    try:
        lexer = Lexer(c_code)
        tokens = lexer.tokenize()

        parser = Parser(tokens)
        ast = parser.parse()

        #  Semantic analysis
        analyzer = SemanticAnalyzer()
        issues = analyzer.analyze(ast)

        warnings = [i.message for i in issues if i.level == "WARNING"]
        errors   = [i.message for i in issues if i.level == "ERROR"]

        if errors:
            error_block = "\n".join(f"[ERROR] {e}" for e in errors)
            warning_block = "\n".join(f"[WARNING] {w}" for w in warnings)
            return (warning_block + "\n" + error_block).strip()
        generator = CodeGenerator()
        python_code = generator.generate(ast)
        if warnings:
            warning_block = "\n".join(f"# [WARNING] {w}" for w in warnings)
            return warning_block + "\n\n" + python_code

        return python_code

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
    app.run(debug=True)
