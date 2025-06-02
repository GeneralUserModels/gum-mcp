# MCP for GUMs

This is a basic instantiation of the Model Context Protocol, with GUMs! 

Simply run the following commands:
```bash
> git clone git@github.com:GeneralUserModels/gum-mcp.git
> cd gum-mcp
> pip install --editable .
```

Create a .env file with your environment variables. Either ```GUM_LM_API_BASE="gum-base-url"``` and ```SCREEN_LM_API_BASE="screen-base-url"```, if you're using an open source model _or_ ```OPENAI_API_KEY="api_key_here"``` if you're using OpenAI models.

Finally, install the MCP client:

```bash
> mcp install server.py -f .env --with gum-ai
```

The MCP should then be enabled in the Claude app.