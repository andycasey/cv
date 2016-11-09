
""" Generate publication list from ADS. """

__author__ = "Andy Casey <andy@astrowizici.st>"

import ads
import os
import unicodedata
import yaml

# ORCID is used to search, and last_name is just for author order
orcid, last_name = ("0000-0003-0174-0564", "Casey")

# Text formatting.
tex_path, tex_template_path = ("cv/publications.tex", "cv/publications.tex.template")
tex_row_template = "\cvhonor{{{title}}}{{{authors}}}{{{year}}}{{{N}}}\n"

def format_authors(article):
    string = "; ".join(article.author[:10])
    if len(article.author) > 10:
        string += " et al."
    return string


# Search for articles.
articles = list(ads.SearchQuery(
    q="orcid:{}".format(orcid), 
    fl=ads.SearchQuery.DEFAULT_FIELDS + ["citation_count", "property", "pub"],
    sort="pubdate+desc", rows=200))

groups = {
    "1st": [],
    "2nd": [],
    "Nth": []
}

citations = []
for article in articles:

    citations.append(article.citation_count)

    # Count citations for thesis, but don't list it as a publication.
    if "Thesis" in article.pub:
        continue

    # Distinguish into first-, second-, or N-th author papers.
    if article.author[0].startswith(last_name + ", "):
        groups["1st"].append(article)

    elif article.author[1].startswith(last_name + ", "):
        groups["2nd"].append(article)

    else:
        groups["Nth"].append(article)

blanks = {
    "H_index": [n for i, n in enumerate(sorted(citations)[::-1]) if n > i][-1],
    "N_citations": sum(citations),
    "N_publications": len(articles),
    "N_first_author_publications": len(groups["1st"]),
    "N_second_author_publications": len(groups["2nd"]),
    "N_nth_author_publications": len(groups["Nth"]),
    "first_author_publications_tex": u"\n".join(
        [unicode(tex_row_template).format(title=a.title[0], N=n, authors=format_authors(a), year=a.year) \
            for n, a in enumerate(groups["1st"], start=1)]),
    "second_author_publications_tex": u"\n".join(
        [unicode(tex_row_template).format(title=a.title[0], N=n, authors=format_authors(a), year=a.year) \
            for n, a in enumerate(groups["2nd"], start=1)]),
    "nth_author_publications_tex": u"\n".join(
        [unicode(tex_row_template).format(title=a.title[0], N=n, authors=format_authors(a), year=a.year) \
            for n, a in enumerate(groups["Nth"], start=1)]),
}

# Generate TeX.
with open(tex_template_path, "r") as fp:
    template = fp.read()
    unicode_contents = unicode(template).format(**blanks)

    new_contents = unicodedata.normalize('NFKD', unicode_contents).encode('ascii','ignore')
 
    if os.path.exists(tex_path):
        with open(tex_path, "r") as fp:
            previous_contents = fp.read()

    else:
        previous_contents = ""

    with open(tex_path, "w") as fp:
        fp.write(new_contents)

# If there is a change to cv/publications.tex, trigger a Travis build by commit.
if new_contents != previous_contents:
    print("Triggering new Travis build.")

    os.system("git add cv/publications.tex")
    os.system("git commit -m 'Updated publications'")
    os.system("git push origin master")

else:
    print("No change to cv/publications.tex")
