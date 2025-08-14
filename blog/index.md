---
layout: default
title: Blog
permalink: /blog/
---

<div class="blog-container">
  <h1>Blog</h1>
  
  <div class="blog-posts">
    {% for post in site.posts %}
      <article class="blog-post-preview">
        <h2 class="post-title">
          <a href="{{ post.url }}">{{ post.title }}</a>
        </h2>
        
        <div class="post-meta">
          <time datetime="{{ post.date | date_to_xmlschema }}">
            {{ post.date | date: "%Y-%m-%d" }}
          </time>
          {% if post.author %}
            <span class="post-author">by {{ post.author }}</span>
          {% endif %}
        </div>
        
        {% if post.description %}
          <p class="post-excerpt">{{ post.description }}</p>
        {% endif %}
        
        <div class="post-excerpt">
          {{ post.excerpt | strip_html | truncatewords: 30 }}
        </div>
        
        <a href="{{ post.url }}" class="read-more">Preberi več →</a>
      </article>
    {% endfor %}
  </div>
  
  {% if paginator.total_pages > 1 %}
    <div class="pagination">
      {% if paginator.previous_page %}
        <a href="{{ paginator.previous_page_path }}" class="previous">← Prejšnja</a>
      {% endif %}
      
      <span class="page_number">
        Stran {{ paginator.page }} od {{ paginator.total_pages }}
      </span>
      
      {% if paginator.next_page %}
        <a href="{{ paginator.next_page_path }}" class="next">Naslednja →</a>
      {% endif %}
    </div>
  {% endif %}
</div>