# AutoLabeller

This GitHub bot is used to recommend solved issues for GFIs, so that new developers can use those recommendations as worked examples.

## Setting Up

1. Setup a GitHub bot [following the GitHub documentation.](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/registering-a-github-app)

2. Install the requirements

```
pip install -r requirements.txt
```

3. Set up config.ini following the example at [config.ini.example](/config.ini.example)

4. Run the bot
```
python index.py
```

## Using

After [installing](https://docs.github.com/en/apps/using-github-apps/installing-your-own-github-app) the bot any new issue that gets labelled as `Good First Issue` will get a comment suggesting a similar, solved, issue.

Note: it's important that the bot is running and setup before installing it, so that it can build up the database with solved issues.