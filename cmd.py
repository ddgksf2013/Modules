import os
import requests
import re


def download_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Ensure request was successful
        return response.text
    except requests.RequestException as e:
        print(f"Error downloading content from {url}: {e}")
        return None

def save_content(content, file_path):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except IOError as e:
        print(f"Error saving content to {file_path}: {e}")

def rewrite_to_sgmodule(js_content, project_name):
    # Check for the presence of the hostname section
    if not re.search(r'hostname', js_content, re.IGNORECASE):
        return None

    # Generate sgmodule content
    sgmodule_content = f"""#!name={project_name}
#!desc=融合版，包括墨鱼去开屏2.0、喜马拉雅、哔哩哔哩、微博、油管、KEEP、贴吧、知乎、高德地图、小红书、网易云、百度地图、什么值得买、菜鸟、彩云天气
#!author=ddgksf2013
#!url=https://github.com/ddgksf2013

[General]



[URL Rewrite]

"""
    
    # Regex patterns
    rewrite_local_pattern = r'^(?!.*#.*)(?!.*;.*)(.*?)\s*url\s+(reject|reject-200|reject-img|reject-dict|reject-array)'
    script_pattern = r'^(?!.*#.*)(.*?)\s*url\s+(script-response-body|script-request-body|script-echo-response|script-request-header|script-response-header|script-analyze-echo-response)\s+(\S+)'
    mitm_local_pattern = r'^\s*hostname\s*=\s*([^\n#]*)\s*(?=#|$)'

    # Process URL rewrite rules
    for match in re.finditer(rewrite_local_pattern, js_content, re.MULTILINE):
        pattern = match.group(1).strip()
        sgmodule_content += f"{pattern} - reject\n"
    sgmodule_content += f"""
[Script]

"""
    # Process script rules
    for match in re.finditer(script_pattern, js_content, re.MULTILINE):
        pattern = match.group(1).strip()
        script_type_raw = match.group(2)
        script_path = match.group(3).strip()
        filename = re.search(r'/([^/]+)$', script_path).group(1)
        
        script_type = 'response' if script_type_raw in ['script-response-body', 'script-echo-response', 'script-response-header'] else 'request'
        needbody = "true" if script_type_raw in ['script-response-body', 'script-echo-response', 'script-response-header', 'script-request-body', 'script-analyze-echo-response'] else "false"
        
        sgmodule_content += f"{filename} = type=http-{script_type}, pattern={pattern}, script-path={script_path}, requires-body={needbody}, max-size=-1, timeout=60\n"

    # Process MITM
    mitm_match_content = ','.join(match.group(1).strip() for match in re.finditer(mitm_local_pattern, js_content, re.MULTILINE))
    sgmodule_content += f"""

[MITM]

hostname = %INSERT% {mitm_match_content}
"""
    return sgmodule_content

def process_urls(urls, project_name):
    combined_js_content = ""
    
    for url in urls:
        js_content = download_content(url)
        if js_content:
            combined_js_content += js_content + "\n"  # Combine content from each URL
        else:
            print(f"Failed to download or process the content from {url}.")

    # Use rewrite_to_sgmodule to process the combined content
    sgmodule_content = rewrite_to_sgmodule(combined_js_content, project_name)
    if sgmodule_content:
        output_file = 'Adblock.sgmodule'
        save_content(sgmodule_content, output_file)
        print(f"Successfully converted and saved to {output_file}")
    else:
        print("Combined content does not meet the requirements for conversion.")

if __name__ == "__main__":
    # Get the script directory
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Build the full path for tmp/1.txt
    input_file_path = os.path.join(current_dir, "tmp", "1.txt")

    # Print the constructed path for verification
    print("Input file path:", input_file_path)

    # Read file content
    try:
        with open(input_file_path, 'r') as file:
            urls = file.readlines()
    except IOError as e:
        print(f"Error reading the input file: {e}")
        exit(1)

    # Define project name (customize as needed)
    project_name = "墨鱼去广告"

    # Process the URLs
    process_urls([url.strip() for url in urls if url.strip()], project_name)
    input("Press Enter to exit...")