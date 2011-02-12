import urlparse

from zope.interface import implements

from zope.component import adapter

from zope.site.hooks import getSite

from zope.publisher.browser import BrowserView

from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm

from plone.resource.traversal import ResourceTraverser
from plone.resource.manifest import getAllResources

from plone.registry.interfaces import IRecordModifiedEvent

from plone.memoize.volatile import cache, store_on_context

from plone.app.blocks.interfaces import SITE_LAYOUT_RESOURCE_NAME
from plone.app.blocks.interfaces import SITE_LAYOUT_FILE_NAME
from plone.app.blocks.interfaces import SITE_LAYOUT_MANIFEST_FORMAT

from plone.app.blocks.utils import resolveResource
from plone.app.blocks.utils import getDefaultSiteLayout
from plone.app.blocks.utils import getLayoutAwareSiteLayout

from Products.CMFCore.utils import getToolByName
from zExceptions import NotFound

class SiteLayoutTraverser(ResourceTraverser):
    """The site layout traverser.
    
    Allows traveral to /++sitelayout++<name> using ``plone.resource`` to fetch
    things stored either on the filesystem or in the ZODB.
    """
    
    name = SITE_LAYOUT_RESOURCE_NAME

class AvailableLayoutsVocabulary(object):
    """Vocabulary to return available layouts of a given type
    """
    
    implements(IVocabularyFactory)
    
    def __init__(self, format, defaultFilename):
        self.format = format
        self.defaultFilename = defaultFilename
    
    def __call__(self, context):
        items = []
        
        resources = getAllResources(self.format)
        for name, manifest in resources.items():
            title = name.capitalize().replace('-', ' ').replace('.', ' ')
            filename = self.defaultFilename
            
            if manifest is not None:
                title = manifest['title'] or title
                filename = manifest['file'] or filename
            
            path = "/++%s++%s/%s" % (self.format.resourceType, name, filename)
            items.append(SimpleTerm(path, name, title))
        
        return SimpleVocabulary(items)

AvailableSiteLayoutsVocabularyFactory = AvailableLayoutsVocabulary(
        SITE_LAYOUT_MANIFEST_FORMAT,
        SITE_LAYOUT_FILE_NAME,
    )

def cacheKey(method, self):
    """Invalidate if the fti is modified, the global registry is modified,
    or the content is modified
    """
    
    catalog = getToolByName(self.context, 'portal_catalog')
    
    return (
            getattr(self.context, '_p_mtime', None),
            catalog.getCounter(),
        )

@adapter(IRecordModifiedEvent)
def globalSiteLayoutModified(event):
    """Invalidate caches if the global site layout is changed. This will
    likely also affect things cached using plone.app.caching, which is what
    we want - the page has probably changed
    """
    if event.record.__name__ == 'plone.defaultSiteLayout':
        if event.oldValue != event.newValue:
            catalog = getToolByName(getSite(), 'portal_catalog', None)
            if catalog is not None and hasattr(catalog, '_increment_counter'):
                catalog._increment_counter()

class DefaultSiteLayout(BrowserView):
    """Look up and render the site layout to use for the context.
    
    Use this for a page that does not have the ILayout behavior, or a
    standalone page template.
    
    The idea is that you can do:
    
        <link rel="layout" href="./@@default-site-layout" />
        
    and always get the correct site layout for the page, taking section-
    specific settings into account.
    """
    
    @cache(cacheKey, store_on_context)
    def __call__(self):
        layout = getDefaultSiteLayout(self.context)
        if layout is None:
            raise NotFound("No default site layout set")
            
        path = urlparse.urljoin(self.context.absolute_url_path(), layout)
        return resolveResource(path)

class PageSiteLayout(BrowserView):
    """Look up and render the site layout to use for the context.
    
    Use this for a page that does have the ILayout behavior. It will take the
    ``pageSiteLayout`` property into account.
    
    The idea is that you can do:
    
        <link rel="layout" href="./@@page-site-layout" />
        
    and always get the correct site layout for the page, taking section-
    and page-specific settings into account.
    """
    
    @cache(cacheKey, store_on_context)
    def __call__(self):
        layout = getLayoutAwareSiteLayout(self.context)
        if layout is None:
            raise NotFound("No default site layout set")
            
        path = urlparse.urljoin(self.context.absolute_url_path(), layout)
        return resolveResource(path)
