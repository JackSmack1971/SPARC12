# SPARC12 Enhanced Setup Guide

Complete setup guide for integrating your specialized SPARC Context Portal with Roo Code.

## 📁 Project Structure

```
your-project/
├── .roo/
│   ├── mcp.json                    # MCP server configuration
│   └── system-prompt-*             # Optional custom prompts
├── .roomodes                       # Enhanced SPARC modes
├── sparc-server/                   # Your MCP server implementation
│   ├── specialized_mcp_server.py   # Your core implementation
│   ├── sparc_mcp_server.py         # MCP wrapper
│   ├── enhanced_embeddings.py      # Optional embeddings upgrade
│   └── requirements.txt            # Python dependencies
├── context-portal/                 # Database storage
│   └── context.db                 # SQLite database (auto-created)
├── memory-bank/                    # File-based sync layer
│   ├── current-phase.md
│   ├── phases/
│   ├── context/
│   └── ...
└── README.md
```

## 🚀 Installation Steps

### 1. Install Dependencies

```bash
# Core dependencies
pip install scikit-learn mcp

# Optional: Enhanced embeddings
pip install sentence-transformers

# Optional: OpenAI embeddings  
pip install openai
```

### 2. Configure MCP Server

Create `.roo/mcp.json`:

```json
{
  "mcpServers": {
    "sparc-context-portal": {
      "command": "python",
      "args": [
        "./sparc-server/sparc_mcp_server.py",
        "${workspaceFolder}"
      ],
      "env": {
        "PYTHONPATH": "./sparc-server"
      },
      "disabled": false,
      "alwaysAllow": [
        "sparc_get_current_phase",
        "sparc_get_active_context",
        "sparc_rag_assist",
        "sparc_semantic_search"
      ]
    }
  }
}
```

### 3. Install Enhanced SPARC Modes

Save the enhanced `.roomodes` configuration in your project root.

### 4. Initialize the Context Database

```bash
# Initialize with existing memory bank (if you have one)
python sparc-server/specialized_mcp_server.py /path/to/your/project --action import --memory-bank ./memory-bank

# Or start fresh
python sparc-server/specialized_mcp_server.py /path/to/your/project --action status
```

## 🎯 Usage Examples

### Basic Context Management

```python
# In your SPARC modes, you can now use:

# Get current phase
current_phase = sparc_get_current_phase()

# Search for relevant context
results = sparc_rag_assist(
    query="authentication patterns for microservices",
    mode="sparc-architect-enhanced"
)

# Log architectural decisions
sparc_log_decision(
    summary="Chose JWT authentication with refresh tokens",
    rationale="Provides stateless authentication with good security properties...",
    tags=["authentication", "security", "jwt"]
)
```

### Advanced RAG Queries

```python
# Architecture mode queries
sparc_rag_assist("database patterns for high-volume transactions")
sparc_rag_assist("microservices communication patterns")

# Implementation mode queries  
sparc_rag_assist("error handling patterns in Python APIs")
sparc_rag_assist("testing strategies for async functions")

# Security mode queries
sparc_rag_assist("common SQL injection prevention patterns")
sparc_rag_assist("secure configuration management approaches")
```

### Phase Transitions

```python
# Check if ready for next phase
current_phase = sparc_get_current_phase()
relevant_context = sparc_rag_assist(f"completion criteria for {current_phase} phase")

# Transition when ready
sparc_transition_phase(confirm=True)
```

## 🔧 Configuration Options

### Embedding Provider Selection

```python
# In your sparc_mcp_server.py, you can configure:

# Fast, no dependencies (default)
server = EnhancedContextPortalSPARCServer(
    workspace_dir=workspace_path,
    embedding_type="tfidf"
)

# Better semantic understanding
server = EnhancedContextPortalSPARCServer(
    workspace_dir=workspace_path,
    embedding_type="sentence_transformer",
    model_name="all-MiniLM-L6-v2"
)

# Best quality (requires OpenAI API key)
server = EnhancedContextPortalSPARCServer(
    workspace_dir=workspace_path,
    embedding_type="openai",
    api_key="your-openai-key"
)
```

### Custom Mode Configuration

```json
{
  "slug": "sparc-custom-mode",
  "name": "🎨 Custom SPARC Mode",
  "description": "Your specialized mode with context awareness",
  "roleDefinition": "You are a specialized mode with access to project context...",
  "customInstructions": "Always use sparc_rag_assist to get relevant context before making decisions...",
  "groups": ["read", "edit", "mcp"],
  "mcpServers": ["sparc-context-portal"]
}
```

## 📊 Monitoring and Maintenance

### Database Health Checks

```bash
# Check current status
python sparc-server/specialized_mcp_server.py /path/to/project --action status

# Rebuild embeddings if needed
python -c "
from sparc-server.enhanced_embeddings import EnhancedContextPortalSPARCServer
server = EnhancedContextPortalSPARCServer('/path/to/project')
server.rebuild_embeddings()
"
```

### Memory Bank Sync

```bash
# Export database to files
python sparc-server/specialized_mcp_server.py /path/to/project --action export --memory-bank ./memory-bank

# Import files to database  
python sparc-server/specialized_mcp_server.py /path/to/project --action import --memory-bank ./memory-bank
```

## 🛠️ Troubleshooting

### Common Issues

1. **MCP Server Not Starting**
   ```bash
   # Check Python path and dependencies
   python sparc-server/sparc_mcp_server.py /path/to/project
   ```

2. **No Search Results**
   ```bash
   # Rebuild embeddings
   python -c "
   from sparc-server.enhanced_embeddings import EnhancedContextPortalSPARCServer
   server = EnhancedContextPortalSPARCServer('/path/to/project')
   server.rebuild_embeddings()
   "
   ```

3. **Database Corruption**
   ```bash
   # Backup and rebuild from memory bank
   cp context-portal/context.db context-portal/context.db.backup
   rm context-portal/context.db
   python sparc-server/specialized_mcp_server.py /path/to/project --action import --memory-bank ./memory-bank
   ```

### Debug Mode

Add to your MCP configuration:

```json
{
  "mcpServers": {
    "sparc-context-portal": {
      "command": "python",
      "args": ["./sparc-server/sparc_mcp_server.py", "${workspaceFolder}"],
      "env": {
        "PYTHONPATH": "./sparc-server",
        "SPARC_DEBUG": "1"
      }
    }
  }
}
```

## 🎉 What You Get

With this setup, your SPARC modes become incredibly powerful:

### ✨ **Context Awareness**

- Every mode can access the full project history
- Intelligent suggestions based on similar past decisions
- Cross-phase knowledge transfer

### 🔍 **Semantic Search**

- Find relevant patterns and decisions using natural language
- Discover connections between different project aspects
- Learn from previous project experiences

### 📈 **Progressive Intelligence**

- System gets smarter as you use it more
- Builds up organizational knowledge over time
- Shares learnings across projects

### 🚀 **Enhanced Productivity**

- Modes provide context-aware suggestions
- Reduce time spent researching solutions
- Avoid repeating past mistakes

## 🌟 Next Steps

1. **Start Simple**: Begin with TF-IDF embeddings and basic usage
2. **Add Data**: Import existing memory banks and start logging decisions
3. **Upgrade Gradually**: Move to sentence transformers for better search
4. **Customize**: Create specialized modes for your specific workflow
5. **Scale**: Add cross-project knowledge sharing

This enhanced SPARC12 framework transforms your development process from manual
documentation to intelligent, context-aware assistance!
