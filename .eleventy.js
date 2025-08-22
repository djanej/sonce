module.exports = function(eleventyConfig) {
	// Copy uploads to the root-level /uploads folder in the output
	eleventyConfig.addPassthroughCopy({ "static/uploads": "uploads" });
	// Passthrough copy for existing static site files and assets
	eleventyConfig.addPassthroughCopy("robots.txt");
	eleventyConfig.addPassthroughCopy("sw.js");
	eleventyConfig.addPassthroughCopy("sitemap*.xml");
	eleventyConfig.addPassthroughCopy("images");
	eleventyConfig.addPassthroughCopy("favicons");
	eleventyConfig.addPassthroughCopy("podpora.html");
	eleventyConfig.addPassthroughCopy("pogoji-uporabe.html");
	eleventyConfig.addPassthroughCopy("pravilnik-o-piskotkih.html");
	eleventyConfig.addPassthroughCopy("pravilnik-o-zasebnosti.html");
	eleventyConfig.addPassthroughCopy("pristopna-izjava.pdf");
	eleventyConfig.addPassthroughCopy("prospekt-sindikata-sonce-slovenije.pdf");

	// Watch admin and content folders for changes during dev
	eleventyConfig.addWatchTarget("admin/");
	eleventyConfig.addWatchTarget("content/");

	// Shortcodes
	eleventyConfig.addShortcode("year", function() {
		return new Date().getFullYear();
	});

	// Friendly date filter for templates
	eleventyConfig.addFilter("dateDisplay", function(dateValue) {
		try {
			const dateObj = new Date(dateValue);
			return dateObj.toLocaleDateString("sl-SI", { year: "numeric", month: "long", day: "numeric" });
		} catch (e) {
			return dateValue;
		}
	});

	// News collection from content/news/*.md
	eleventyConfig.addCollection("news", function(collectionApi) {
		return collectionApi
			.getFilteredByGlob("content/news/*.md")
			.sort((a, b) => (b.date || 0) - (a.date || 0));
	});

	return {
		dir: {
			input: ".",
			includes: "src/_includes",
			data: "src/_data",
			output: "_site"
		},
		templateFormats: ["njk", "md"],
		markdownTemplateEngine: "njk",
		htmlTemplateEngine: "njk",
		passthroughFileCopy: true
	};
};

