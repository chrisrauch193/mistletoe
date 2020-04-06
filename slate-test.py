import mistletoe
from mistletoe.slate_html_renderer import SlateHTMLRenderer

with open('test.md', 'r') as fin:
    rendered = mistletoe.markdown(fin, SlateHTMLRenderer)

    print(rendered)

    # f = open("_action_type_product_type_linker.html", "r+")
    f = open("test.html", "r+")
    f.write(rendered)
    f.close()

    print("Finished!!")
