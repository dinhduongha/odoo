import { DynamicSnippet } from "@website/snippets/s_dynamic_snippet/dynamic_snippet";
import { registry } from "@web/core/registry";

export class BlogPosts extends DynamicSnippet {
    static selector = ".s_dynamic_snippet_blog_posts";

    /**
     * @override
     */
    getSearchDomain() {
        const searchDomain = super.getSearchDomain(...arguments);
        // uuid record id: keep as string
        const filterByBlogId = this.el.dataset.filterByBlogId;
        if (filterByBlogId) {
            searchDomain.push(["blog_id", "=", filterByBlogId]);
        }
        return searchDomain;
    }
}

registry.category("public.interactions").add("website_blog.blog_posts", BlogPosts);

registry.category("public.interactions.edit").add("website_blog.blog_posts", {
    Interaction: BlogPosts,
});

registry.category("public.interactions.preview").add("website_blog.blog_posts", {
    Interaction: BlogPosts,
});
