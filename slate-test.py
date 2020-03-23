import mistletoe
from mistletoe.slate_html_renderer import SlateHTMLRenderer

with open('_action_types.md', 'r') as fin:
    rendered = mistletoe.markdown(fin, SlateHTMLRenderer)

    print(rendered)

    f = open("_action_types.html", "a")
    f.write(rendered)
    f.close()

    print("Finished!!")