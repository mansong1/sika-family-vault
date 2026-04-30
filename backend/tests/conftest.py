import sys
import os
sys.path.insert(0, "/root/builds/sika-family-vault/backend")

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["DEBUG"] = "true"
