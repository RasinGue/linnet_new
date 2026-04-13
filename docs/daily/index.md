---
layout: default
title: Daily Digest
nav_order: 2
has_children: false
---

# 日报存档

{% assign daily_pages = site.pages | where_exp: "p", "p.dir == '/daily/'" | sort: "name" | reverse %}
{% for page in daily_pages %}
{% unless page.name == "index.md" %}
- [{{ page.title }}]({{ page.url | relative_url }})
{% endunless %}
{% endfor %}
