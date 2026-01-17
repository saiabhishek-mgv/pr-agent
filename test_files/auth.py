# auth.py - Authentication module with issues

from flask import request

# Security Issue: XSS vulnerability
def display_user_input():
    user_input = request.args.get('name')
    # Vulnerable to XSS
    return f"<div>{user_input}</div>"

# Security Issue: Using eval
def calculate(expression):
    # Dangerous use of eval
    return eval(expression)

# Security Issue: Unsafe YAML loading
import yaml
def load_config(config_file):
    with open(config_file) as f:
        # Should use yaml.safe_load()
        return yaml.load(f)

# Security Issue: innerHTML usage in JavaScript-like pattern
def render_html(content):
    # This simulates JavaScript innerHTML usage
    element_innerHTML = content  # Vulnerable pattern
    return element_innerHTML
