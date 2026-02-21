project('betternotes',
  version: '0.1.1',
  meson_version: '>= 0.62.0',
  default_options: ['warning_level=2'],
)

gnome = import('gnome')
python = import('python')

py_installation = python.find_installation('python3')

pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'betternotes'

conf = configuration_data()
conf.set('PYTHON', py_installation.full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)
conf.set('APP_ID', 'com.github.souren.BetterNotes')

subdir('data')
subdir('src')

gnome.post_install(
  glib_compile_schemas: true,
  gtk_update_icon_cache: true,
  update_desktop_database: true,
)
