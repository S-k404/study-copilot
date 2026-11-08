"""
Local Mock Practice Server for Testing Screen-Reading & Explainer Assistants.
Runs a local web server at http://127.0.0.1:8000
"""

import http.server
import socketserver
import webbrowser
import sys

PORT = 8000

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Practice Quiz Sandbox - Algorithms & Machine Learning</title>
  <style>
    :root {
      --primary: #0056D2;
      --bg: #F5F7FA;
      --card-bg: #FFFFFF;
      --text: #1F1F1F;
      --border: #D1D5DB;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
      margin: 0;
      padding: 40px 20px;
    }
    .container {
      max-width: 760px;
      margin: 0 auto;
    }
    .header {
      background: var(--card-bg);
      padding: 24px;
      border-radius: 8px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
      margin-bottom: 24px;
      border-left: 5px solid var(--primary);
    }
    .header h1 {
      margin: 0 0 8px 0;
      font-size: 24px;
    }
    .header p {
      margin: 0;
      color: #555;
      font-size: 14px;
    }
    .quiz-card {
      background: var(--card-bg);
      padding: 24px;
      border-radius: 8px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
      margin-bottom: 20px;
    }
    .question-title {
      font-weight: 600;
      font-size: 16px;
      margin-bottom: 12px;
    }
    .code-block {
      background: #282C34;
      color: #ABB2BF;
      padding: 12px 16px;
      border-radius: 6px;
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
      font-size: 13px;
      margin: 10px 0 14px 0;
      overflow-x: auto;
    }
    .options label {
      display: flex;
      align-items: center;
      padding: 10px 14px;
      margin-bottom: 8px;
      border: 1px solid var(--border);
      border-radius: 6px;
      cursor: pointer;
      transition: background 0.15s, border-color 0.15s;
    }
    .options label:hover {
      background: #F0F4FF;
      border-color: var(--primary);
    }
    .options input[type="radio"] {
      margin-right: 12px;
      accent-color: var(--primary);
    }
    .actions {
      display: flex;
      justify-content: flex-end;
      gap: 12px;
      margin-top: 24px;
    }
    button {
      background: var(--primary);
      color: white;
      border: none;
      padding: 10px 20px;
      border-radius: 6px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
    }
    button.secondary {
      background: #E5E7EB;
      color: #374151;
    }
    .badge {
      display: inline-block;
      background: #EBF3FF;
      color: var(--primary);
      font-size: 12px;
      font-weight: bold;
      padding: 2px 8px;
      border-radius: 4px;
      margin-bottom: 8px;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <span class="badge">OFFLINE STUDY SANDBOX</span>
      <h1>Week 3 Practice: Algorithms & Optimization</h1>
      <p>Use this mock practice exam to test your screen reading assistant, concept explainer, and menu bar shortcuts.</p>
    </div>

    <!-- Question 1 -->
    <div class="quiz-card" id="q1">
      <div class="question-title">1. What is the worst-case time complexity of standard QuickSort with a naive first-element pivot strategy?</div>
      <div class="options">
        <label><input type="radio" name="q1" value="A"> A) O(N log N)</label>
        <label><input type="radio" name="q1" value="B"> B) O(N^2)</label>
        <label><input type="radio" name="q1" value="C"> C) O(N)</label>
        <label><input type="radio" name="q1" value="D"> D) O(log N)</label>
      </div>
    </div>

    <!-- Question 2 -->
    <div class="quiz-card" id="q2">
      <div class="question-title">2. Consider the following Python snippet. What will be the output?</div>
      <div class="code-block">
def append_val(val, target_list=[]):
    target_list.append(val)
    return target_list

print(append_val(1))
print(append_val(2))
      </div>
      <div class="options">
        <label><input type="radio" name="q2" value="A"> A) [1] followed by [2]</label>
        <label><input type="radio" name="q2" value="B"> B) [1] followed by [1, 2]</label>
        <label><input type="radio" name="q2" value="C"> C) TypeError: default argument mutated</label>
        <label><input type="radio" name="q2" value="D"> D) [1, 1] followed by [2, 2]</label>
      </div>
    </div>

    <!-- Question 3 -->
    <div class="quiz-card" id="q3">
      <div class="question-title">3. In Gradient Descent optimization, what is the most likely consequence of setting the learning rate (alpha) excessively high?</div>
      <div class="options">
        <label><input type="radio" name="q3" value="A"> A) The optimization algorithm converges prematurely to a saddle point.</label>
        <label><input type="radio" name="q3" value="B"> B) The loss function oscillates wildly and diverges rather than converging to a minimum.</label>
        <label><input type="radio" name="q3" value="C"> C) The gradients vanish to zero after the first epoch.</label>
        <label><input type="radio" name="q3" value="D"> D) Computational cost per step increases exponentially.</label>
      </div>
    </div>

    <div class="actions">
      <button class="secondary" onclick="alert('Answers reset.')">Reset</button>
      <button onclick="checkAnswers()">Check Answers</button>
    </div>
  </div>

  <script>
    function checkAnswers() {
      const q1 = document.querySelector('input[name="q1"]:checked')?.value;
      const q2 = document.querySelector('input[name="q2"]:checked')?.value;
      const q3 = document.querySelector('input[name="q3"]:checked')?.value;
      
      let results = [];
      results.push("Q1: " + (q1 === "B" ? "✅ Correct (B)" : "❌ Incorrect (Correct is B)"));
      results.push("Q2: " + (q2 === "B" ? "✅ Correct (B)" : "❌ Incorrect (Correct is B - default mutable arg trap)"));
      results.push("Q3: " + (q3 === "B" ? "✅ Correct (B)" : "❌ Incorrect (Correct is B - divergence from overshooting)"));
      
      alert(results.join("\\n"));
    }
  </script>
</body>
</html>
"""

class MockQuizHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(HTML_PAGE.encode("utf-8"))

def run_server():
    with socketserver.TCPServer(("127.0.0.1", PORT), MockQuizHandler) as httpd:
        print(f"Mock practice quiz running at http://127.0.0.1:{PORT}")
        print("Press Ctrl+C to stop server.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--open":
        webbrowser.open(f"http://127.0.0.1:{PORT}")
    run_server()

