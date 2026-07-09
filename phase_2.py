import asyncio
import aiohttp
import os
import sys
import re
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter

async def fetch_repo_tree(session, owner, repo, branch, token=None):
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
        
    async with session.get(url, headers=headers) as response:
        if response.status != 200:
            return []
        data = await response.json()
        return data.get("tree", [])

async def download_file(session, owner, repo, branch, path, token=None, semaphore=None):
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
        
    async with semaphore:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.text()
            else:
                return None

def is_programming_logic_file(path):
    logic_extensions = {".py", ".java", ".cpp", ".c", ".h", ".js", ".ts", ".go", ".rs", ".rb", ".php"}
    _, ext = os.path.splitext(path)
    return ext.lower() in logic_extensions

async def get_github_code_chunks(max_files_per_repo=5):
    github_token = os.environ.get("GITHUB_TOKEN")
    
    username = "encode" # fallback
    if os.path.exists("github_config.json"):
        with open("github_config.json", "r") as f:
            data = json.load(f)
            username = data.get("github_username", "encode")
            
    print(f"Targeting GitHub User: {username}")
    
    async with aiohttp.ClientSession() as session:
        # Fetch list of repos for the user
        repos_url = f"https://api.github.com/users/{username}/repos"
        headers = {"Accept": "application/vnd.github.v3+json"}
        if github_token: headers["Authorization"] = f"token {github_token}"
        
        async with session.get(repos_url, headers=headers) as resp:
            if resp.status != 200:
                print(f"Failed to fetch repositories for user {username}")
                return []
            repos = await resp.json()
            
        all_raw_texts = []
        semaphore = asyncio.Semaphore(10)
        
        for repo_obj in repos:
            repo_name = repo_obj["name"]
            branch = repo_obj.get("default_branch", "main")
            print(f"Scanning repository: {repo_name}...")
            
            tree = await fetch_repo_tree(session, username, repo_name, branch, github_token)
            if not tree:
                # Try master if main failed
                branch = "master"
                tree = await fetch_repo_tree(session, username, repo_name, branch, github_token)
                
            logic_files = [item["path"] for item in tree if item["type"] == "blob" and is_programming_logic_file(item["path"])]
            
            if len(logic_files) > max_files_per_repo:
                logic_files = logic_files[:max_files_per_repo]
                
            download_tasks = [download_file(session, username, repo_name, branch, path, github_token, semaphore) for path in logic_files]
            file_contents = await asyncio.gather(*download_tasks)
            
            for path, content in zip(logic_files, file_contents):
                if content:
                    file_text = f"--- Repository: {repo_name} | File: {path} ---\n{content}\n"
                    all_raw_texts.append(file_text)
                    
        if not all_raw_texts:
            return []
            
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
        )
        
        all_chunks = []
        for text in all_raw_texts:
            chunks = text_splitter.split_text(text)
            all_chunks.extend(chunks)
            
        return all_chunks

async def main():
    print("Fetching and chunking code from all repositories...")
    chunks = await get_github_code_chunks()
    print(f"Total semantic chunks generated: {len(chunks)}")

if __name__ == "__main__":
    asyncio.run(main())
