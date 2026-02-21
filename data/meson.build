install_data(
  'com.github.souren.BetterNotes.desktop.in',
  rename: 'com.github.souren.BetterNotes.desktop',
  install_dir: get_option('datadir') / 'applications',
)

install_data(
  'com.github.souren.BetterNotes.metainfo.xml.in',
  rename: 'com.github.souren.BetterNotes.metainfo.xml',
  install_dir: get_option('datadir') / 'metainfo',
)

install_data(
  'com.github.souren.BetterNotes.gschema.xml',
  install_dir: get_option('datadir') / 'glib-2.0' / 'schemas',
)

install_data(
  'icons/hicolor/scalable/apps/com.github.souren.BetterNotes.svg',
  install_dir: get_option('datadir') / 'icons' / 'hicolor' / 'scalable' / 'apps',
)

# Install CSS for loading at runtime
install_data(
  'resources/style.css',
  install_dir: pkgdatadir,
)

# GResource compilation — requires glib-compile-resources (available in Flatpak SDK)
if find_program('glib-compile-resources', required: false).found()
  gnome.compile_resources(
    'betternotes',
    'resources/betternotes.gresource.xml',
    gresource_bundle: true,
    install: true,
    install_dir: pkgdatadir,
    source_dir: 'resources',
  )
endif
