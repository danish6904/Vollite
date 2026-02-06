import hashlib
import os
import random
import string

def calculate_score(content):
    """Calculate the score exactly as app.py does"""
    sha256 = hashlib.sha256(content.encode()).hexdigest()
    file_hash_int = int(sha256[:8], 16)
    return file_hash_int % 100

def generate_content_for_score(target_range, min_size_kb=1024):
    """
    Mine for a random string that produces a hash score within target_range.
    Also ensures file size is decent.
    """
    # Base content to ensure size
    base_content = "".join(random.choices(string.ascii_letters, k=min_size_kb * 1024))
    
    attempts = 0
    while True:
        attempts += 1
        # Add random suffix to change hash
        suffix = str(random.random())
        candidate = base_content + suffix
        score = calculate_score(candidate)
        
        if target_range[0] <= score <= target_range[1]:
            print(f"Found match! Score: {score} (Attempts: {attempts})")
            return candidate

def main():
    output_dir = "sample_dumps"
    os.makedirs(output_dir, exist_ok=True)
    
    targets = [
        {
            "filename": "Clean_System_Snapshot.dmp",
            "range": (0, 29),
            "desc": "Triggers 'Clean System' (Low Risk)"
        },
        {
             "filename": "Start_Ups_Financials.dmp",
             "range": (50, 79),
             "desc": "Triggers 'C2 Data Exfiltration' (Medium/High Risk)"
        },
        {
            "filename": "Infected_Ransomware.dmp",
            "range": (81, 99),
            "desc": "Triggers 'Ransomware Attack' (Critical Risk)"
        }
    ]
    
    print("Generating consistent sample files...")
    
    for t in targets:
        print(f"Mining content for {t['filename']} ({t['desc']})...")
        content = generate_content_for_score(t['range'])
        
        path = os.path.join(output_dir, t['filename'])
        with open(path, 'w') as f:
            f.write(content)
        print(f"Created {path}\n")
        
    print("Done! Use these files to demonstrate specific scenarios.")

if __name__ == "__main__":
    main()
