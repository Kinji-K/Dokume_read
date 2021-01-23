from DokumeRead import DokumeRead
from WriteWiki import WriteWiki
from Slack import SlackPost

def main():
    DokumeRead()
    WriteWiki()
    slack = SlackPost()
    slack.WebhookSlack("wikiの更新が完了しました")

if __name__ == "__main__":
    main()