import mimetypes
import magic
import logging
import os

from ckan.logic import ValidationError
from ckan.common import config

log = logging.getLogger(__name__)

DEFAULT_UPLOAD_BLACKLIST = ['.exe']
DEFAULT_EXTENDED_UPLOAD_MIMETYPES = { 'application/x-dosexec': '.exe' }

def _add_mimetypes():
    if not mimetypes.inited:
        mimetypes.init()

    # Add mimetypes from config
    config_mimetypes = eval(config.get('ckanext.security.extended_upload_mimetypes', '{}'))
    extended_mimetypes = DEFAULT_EXTENDED_UPLOAD_MIMETYPES.copy()
    extended_mimetypes.update(config_mimetypes) # merges defaults and config

    for mime in extended_mimetypes:
        mimetypes.add_type(mime, extended_mimetypes[mime], strict=False)

def _build_mimetypes_and_extensions(filename, file_content):
    mimes_instance = mimetypes.MimeTypes()
    extensions_and_mimetypes = []

    # get supplied file extension and possible mimetypes for that extension
    _, supplied_file_extension = os.path.splitext(filename)
    if supplied_file_extension:
        extensions_and_mimetypes.append(supplied_file_extension)

        guessed_mimetypes = filter(lambda type: type is not None, [
            mimes_instance.types_map[0].get(supplied_file_extension),
            mimes_instance.types_map[1].get(supplied_file_extension)
        ])
        extensions_and_mimetypes.extend(guessed_mimetypes)

    if file_content:
        # get inferred mimetype of file and possible extensions for that mimetype
        try:
            # try to get python-magic to infer upload file mime type from actual file content
            mimetype = magic.from_buffer(file_content.read(2048), mime=True)
        except IOError:
            log.warning('Unable to detect mimetype from file content')

        if mimetype:
            extensions_and_mimetypes.append(mimetype)

            # build set of possible extensions for the mimetype
            nonstandard_extensions = mimes_instance.types_map_inv[0].get(mimetype, [])
            standard_extensions = mimes_instance.types_map_inv[1].get(mimetype, [])
            extensions_and_mimetypes.extend(nonstandard_extensions)
            extensions_and_mimetypes.extend(standard_extensions)

    unique_set = set(extensions_and_mimetypes)
    unique_list = list(unique_set)

    return unique_list

def validate_upload_type(resource):
    """
    Uses the mimetypes builtin library to make inferences about the filename
    and test the possible mimetypes and extensions against the blacklist.
    Also uses python-magic to attempt detection of the mimetype by file contents.

    NOTE: When linking files rather than uploading, we only test the extension at present.
    """
    try:
        uploaded_file = resource.get('upload').file
    except AttributeError:
        uploaded_file = None

    _add_mimetypes()
    extensions_and_mimetypes = _build_mimetypes_and_extensions(resource.get('url'), uploaded_file)

    config_blacklist = eval(config.get('ckanext.security.upload_blacklist', '[]'))
    blacklist = list(DEFAULT_UPLOAD_BLACKLIST)
    blacklist.extend(config_blacklist)

    log.info('Detected extensions/mimetypes: {}'.format(extensions_and_mimetypes))
    # test all extensions and mimetypes against blacklist, fail fast
    if any(map(lambda ext: ext in blacklist, extensions_and_mimetypes)):
        log.warning('Prevented upload of {}, detected mimetypes/extensions: {}, blacklist: {}'.format(resource.get('url'), extensions_and_mimetypes, blacklist))
        resource['url'] = ''
        action = 'upload' if uploaded_file else 'link'
        raise ValidationError(
            {'File': ['Cannot {} files of this type'.format(action)]}
        )

def validate_upload_presence(resource):
    if not resource.get('url'):
        raise ValidationError(
            {'File': ['Please upload a file or link to an external resource']}
        )
