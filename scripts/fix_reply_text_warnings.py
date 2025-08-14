"""
Script to automatically fix 'reply_text is not a known attribute of None' warnings in main.py
"""
import re
import os
from pathlib import Path

def fix_reply_text_warnings(file_path: str):
    """
    Fixes 'reply_text is not a known attribute of None' warnings in the specified file.
    
    Args:
        file_path: Path to the file to fix
    """
    # Read the file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to find update.message.reply_text() calls
    pattern = r'(\s*)(update\.message\.reply_text\()'
    
    # Replacement pattern
    replacement = r'\1from utils.message_utils import safe_reply_text\n\1safe_reply_text(update, '
    
    # Replace all occurrences
    new_content = re.sub(pattern, replacement, content)
    
    # Add import at the top if needed
    if 'from utils.message_utils import safe_reply_text' not in new_content:
        # Find the first import statement
        import_match = re.search(r'^(\s*import\s+\w+)', new_content, re.MULTILINE)
        if import_match:
            # Insert after the first import
            new_content = new_content.replace(
                import_match.group(0),
                f"{import_match.group(0)}\nfrom utils.message_utils import safe_reply_text"
            )
        else:
            # Insert after the docstring if no imports found
            docstring_end = re.search(r'(""".*?"""\s*)', new_content, re.DOTALL)
            if docstring_end:
                new_content = (
                    new_content[:docstring_end.end()] + 
                    '\nfrom utils.message_utils import safe_reply_text\n' + 
                    new_content[docstring_end.end():]
                )
            else:
                # Just add at the top if no docstring found
                new_content = 'from utils.message_utils import safe_reply_text\n' + new_content
    
    # Write the fixed content back to the file
    if new_content != content:
        # Create a backup first
        backup_path = file_path + '.bak'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Write the new content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"Fixed {file_path}. Original saved as {backup_path}")
    else:
        print("No changes were needed.")

if __name__ == "__main__":
    # Path to main.py relative to this script
    script_dir = Path(__file__).parent.parent
    main_py_path = script_dir / 'main.py'
    
    if not main_py_path.exists():
        print(f"Error: {main_py_path} not found.")
    else:
        fix_reply_text_warnings(str(main_py_path))
