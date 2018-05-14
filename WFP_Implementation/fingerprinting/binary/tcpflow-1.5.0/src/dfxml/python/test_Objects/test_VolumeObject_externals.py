
import logging
import os
import xml.etree.ElementTree as ET

_logger = logging.getLogger(os.path.basename(__file__))
logging.basicConfig(level=logging.DEBUG)

import Objects

XMLNS_TEST_CLAMSCAN = "file:///opt/local/bin/clamscan"
XMLNS_TEST_UNREGGED = "file:///dev/random"

ET.register_namespace("clam", XMLNS_TEST_CLAMSCAN)

vo = Objects.VolumeObject()

#Try and fail to add a non-Element to the list.
failed = None
_logger.debug("Before:  " + repr(vo.externals))
try:
    vo.externals.append(1)
    failed = False
except TypeError:
    failed = True
except:
    failed = True
    raise
_logger.debug("After:  " + repr(vo.externals))
assert failed
failed = None

#Dummy up a non-DFXML namespace element.  This should be appendable.
e = ET.Element("{%s}scan_results" % XMLNS_TEST_CLAMSCAN)
e.text = "Clean file system"
vo.externals.append(e)

#Dummy up a DFXML namespace element.  This should not be appendable (the schema specifies other namespaces).
e = ET.Element("{%s}filename" % Objects.dfxml.XMLNS_DFXML)
e.text = "Superfluous name"
_logger.debug("Before:  " + repr(vo.externals))
try:
    vo.externals.append(e)
    failed = False
except ValueError:
    failed = True
except:
    failed = True
    raise
_logger.debug("After:  " + repr(vo.externals))
assert failed
failed = None

#Add an element with the colon prefix style
e = ET.Element("clam:version")
e.text = "20140101"
vo.externals.append(e)

#Add an element that doesn't have an ET-registered namespace prefix.
e = ET.Element("{%s}test2" % XMLNS_TEST_UNREGGED)
e.text = "yes"
vo.externals.append(e)

#Test serialization
s = Objects._ET_tostring(vo.to_Element()) #TODO Maybe this should be more than an internal function.
_logger.debug(s)
if s.find("scan_results") == -1:
    raise ValueError("Serialization did not output other-namespace element 'scan_results'.")
if s.find("clam:version") == -1:
    raise ValueError("Serialization did not output prefixed element 'clam:version'.")
if s.find("test2") == -1:
    raise ValueError("Serialization did not output unregistered-prefix element 'test2'.")

#Test de-serialization
vor = Objects.VolumeObject()
x = ET.XML(s)
vor.populate_from_Element(x)
_logger.debug("De-serialized: %r." % vor.externals)
assert len(vor.externals) == 3
