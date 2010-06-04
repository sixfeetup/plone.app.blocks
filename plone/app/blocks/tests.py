import unittest2 as unittest
import doctest
from plone.testing import layered

from plone.app.testing import PLONE_FUNCTIONAL_TESTING
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import quickInstallProduct

from zope.configuration import xmlconfig

optionflags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)

class PABlocks(PloneSandboxLayer):
    defaultBases = (PLONE_FUNCTIONAL_TESTING,)

    def setUpPloneSite(self, portal):
        
        # load ZCML
        import plone.app.blocks
        import plone.tiles
        xmlconfig.file('configure.zcml', plone.app.blocks,
                       context=self['configurationContext'])

        # install into the Plone site
        quickInstallProduct(portal, 'plone.app.blocks')


PABLOCKS_FUNCTIONAL_TESTING = PABlocks()

def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([
        layered(doctest.DocFileSuite('rendering.txt', 'esi.txt', 'context.txt',
                                     optionflags=optionflags),
                layer=PABLOCKS_FUNCTIONAL_TESTING)
        ])
    return suite
        
