



t91-labuser064582@2-4-582 MINGW64 /c/agentic_ai_course/smart_banking_assistant (main)
$ git init
Reinitialized existing Git repository in C:/agentic_ai_course/smart_banking_assistant/.git/

t91-labuser064582@2-4-582 MINGW64 /c/agentic_ai_course/smart_banking_assistant (main)
$ git branch
  backup-before-secret-cleanup
* main

t91-labuser064582@2-4-582 MINGW64 /c/agentic_ai_course/smart_banking_assistant (main)
$ git status
On branch main
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
        modified:   main.py
        modified:   pyproject.toml
        modified:   src/api/v1/agents/agents.py
        modified:   src/api/v1/routes/query.py
        modified:   src/api/v1/routes/upload_routes.py
        modified:   src/api/v1/schemas/query_schema.py
        modified:   src/api/v1/services/upload_service.py
        modified:   src/api/v1/states/rag_state.py
        modified:   src/api/v1/tools/classifier_tool.py
        modified:   src/api/v1/tools/response_tool.py
        modified:   src/api/v1/tools/search_tool.py
        modified:   src/core/db.py
        modified:   src/core/prompts.py
        modified:   src/ingestion/ingestion.py
        modified:   ui/streamlit_app.py
        modified:   uv.lock

Untracked files:
  (use "git add <file>..." to include in what will be committed)
        banking_agent.png
        src/api/v1/schemas/upload_schema.py

no changes added to commit (use "git add" and/or "git commit -a")

t91-labuser064582@2-4-582 MINGW64 /c/agentic_ai_course/smart_banking_assistant (main)
$ git remote -v
origin  https://github.com/kapilarorabatch3/Smart_Banking_Assistant.git (fetch)
origin  https://github.com/kapilarorabatch3/Smart_Banking_Assistant.git (push)

t91-labuser064582@2-4-582 MINGW64 /c/agentic_ai_course/smart_banking_assistant (main)
$ git remote remove origin

t91-labuser064582@2-4-582 MINGW64 /c/agentic_ai_course/smart_banking_assistant (main)
$ git remote add origin https://github.com/shanmugaraj-ds/Smart_Banking_Assitant.git

t91-labuser064582@2-4-582 MINGW64 /c/agentic_ai_course/smart_banking_assistant (main)
$ git remote -v
origin  https://github.com/shanmugaraj-ds/Smart_Banking_Assitant.git (fetch)
origin  https://github.com/shanmugaraj-ds/Smart_Banking_Assitant.git (push)

t91-labuser064582@2-4-582 MINGW64 /c/agentic_ai_course/smart_banking_assistant (main)
$ git commit -m "smart banking updates"
On branch main
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
        modified:   main.py
        modified:   pyproject.toml
        modified:   src/api/v1/agents/agents.py
        modified:   src/api/v1/routes/query.py
        modified:   src/api/v1/routes/upload_routes.py
        modified:   src/api/v1/schemas/query_schema.py
        modified:   src/api/v1/services/upload_service.py
        modified:   src/api/v1/states/rag_state.py
        modified:   src/api/v1/tools/classifier_tool.py
        modified:   src/api/v1/tools/response_tool.py
        modified:   src/api/v1/tools/search_tool.py
        modified:   src/core/db.py
        modified:   src/core/prompts.py
        modified:   src/ingestion/ingestion.py
        modified:   ui/streamlit_app.py
        modified:   uv.lock

Untracked files:
  (use "git add <file>..." to include in what will be committed)
        banking_agent.png
        src/api/v1/schemas/upload_schema.py

no changes added to commit (use "git add" and/or "git commit -a")

t91-labuser064582@2-4-582 MINGW64 /c/agentic_ai_course/smart_banking_assistant (main)
$ git commit -m "smart banking updates"
On branch main
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
        modified:   main.py
        modified:   pyproject.toml
        modified:   src/api/v1/agents/agents.py
        modified:   src/api/v1/routes/query.py
        modified:   src/api/v1/routes/upload_routes.py
        modified:   src/api/v1/schemas/query_schema.py
        modified:   src/api/v1/services/upload_service.py
        modified:   src/api/v1/states/rag_state.py
        modified:   src/api/v1/tools/classifier_tool.py
        modified:   src/api/v1/tools/response_tool.py
        modified:   src/api/v1/tools/search_tool.py
        modified:   src/core/db.py
        modified:   src/core/prompts.py
        modified:   src/ingestion/ingestion.py
        modified:   ui/streamlit_app.py
        modified:   uv.lock

Untracked files:
  (use "git add <file>..." to include in what will be committed)
        banking_agent.png
        src/api/v1/schemas/upload_schema.py

no changes added to commit (use "git add" and/or "git commit -a")

t91-labuser064582@2-4-582 MINGW64 /c/agentic_ai_course/smart_banking_assistant (main)
$ git add.
git: 'add.' is not a git command. See 'git --help'.

The most similar command is
        add

t91-labuser064582@2-4-582 MINGW64 /c/agentic_ai_course/smart_banking_assistant (main)
$ git add .
warning: in the working copy of 'main.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'pyproject.toml', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'uv.lock', LF will be replaced by CRLF the next time Git touches it

t91-labuser064582@2-4-582 MINGW64 /c/agentic_ai_course/smart_banking_assistant (main)
$ git commit -m "smart banking updates"
[main 402c629] smart banking updates
 18 files changed, 1122 insertions(+), 621 deletions(-)
 create mode 100644 banking_agent.png
 create mode 100644 src/api/v1/schemas/upload_schema.py

t91-labuser064582@2-4-582 MINGW64 /c/agentic_ai_course/smart_banking_assistant (main)
$ git push
fatal: The current branch main has no upstream branch.
To push the current branch and set the remote as upstream, use

    git push --set-upstream origin main

To have this happen automatically for branches without a tracking
upstream, see 'push.autoSetupRemote' in 'git help config'.


t91-labuser064582@2-4-582 MINGW64 /c/agentic_ai_course/smart_banking_assistant (main)
$ ^C

t91-labuser064582@2-4-582 MINGW64 /c/agentic_ai_course/smart_banking_assistant (main)
$  git push --set-upstream origin main
To https://github.com/shanmugaraj-ds/Smart_Banking_Assitant.git
 ! [rejected]        main -> main (fetch first)
error: failed to push some refs to 'https://github.com/shanmugaraj-ds/Smart_Banking_Assitant.git'
hint: Updates were rejected because the remote contains work that you do not
hint: have locally. This is usually caused by another repository pushing to
hint: the same ref. If you want to integrate the remote changes, use
hint: 'git pull' before pushing again.
hint: See the 'Note about fast-forwards' in 'git push --help' for details.

t91-labuser064582@2-4-582 MINGW64 /c/agentic_ai_course/smart_banking_assistant (main)
$ ^C

t91-labuser064582@2-4-582 MINGW64 /c/agentic_ai_course/smart_banking_assistant (main)
$ git pull --rebase origin main
remote: Enumerating objects: 2, done.
remote: Counting objects: 100% (2/2), done.
remote: Compressing objects: 100% (2/2), done.
remote: Total 2 (delta 0), reused 2 (delta 0), pack-reused 0 (from 0)
Unpacking objects: 100% (2/2), 204 bytes | 9.00 KiB/s, done.
From https://github.com/shanmugaraj-ds/Smart_Banking_Assitant
 * branch            main       -> FETCH_HEAD
 * [new branch]      main       -> origin/main
Successfully rebased and updated refs/heads/main.

t91-labuser064582@2-4-582 MINGW64 /c/agentic_ai_course/smart_banking_assistant (main)
$ git push -u origin main
Enumerating objects: 121, done.
Counting objects: 100% (121/121), done.
Delta compression using up to 4 threads
Compressing objects: 100% (96/96), done.
Writing objects: 100% (120/120), 2.13 MiB | 4.66 MiB/s, done.
Total 120 (delta 34), reused 22 (delta 3), pack-reused 0 (from 0)
remote: Resolving deltas: 100% (34/34), done.
To https://github.com/shanmugaraj-ds/Smart_Banking_Assitant.git
   8160cf2..530cf12  main -> main
branch 'main' set up to track 'origin/main'.


env variable -

COHERE_API_KEY=
OPENAI_API_KEY=
OPENAI_MODEL="gpt-4o-mini"
OPENAI_EMBEDDING_MODEL="text-embedding-3-small"


# PGVector store connection (used by LangChain PGVector for document embeddings)
PG_VECTOR_CONNECTION_STRING=postgresql+psycopg://postgres:Pass%40123@localhost:5433/smart_banking_db


# RDSMB related - separate database may be running in different ip address
PG_RDBMS_CONNECTION_STRING=postgresql://banking_readonly:banking_readonly_pass@localhost:5433/core_banking_db

SQL_DATABASE_URI=postgresql+psycopg://banking_readonly:banking_readonly_pass@localhost:5433/core_banking_db


RETRY_THRESHOLD=0.50
max_retries=2

LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=
LANGSMITH_PROJECT="capstone2_project"
t91-labuser064582@2-4-582 MINGW64 /c/agentic_ai_course/smart_banking_assistant (main)
$ A
