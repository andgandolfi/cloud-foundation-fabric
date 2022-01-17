#!/usr/bin/env python3

# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import difflib
import enum
import pathlib

import click
import tfdoc


BASEDIR = pathlib.Path(__file__).resolve().parents[1]


State = enum.Enum('State', 'OK FAIL SKIP')


def _check_dir(dir_name, files=False, show_extra=False):
  dir_path = BASEDIR / dir_name
  for readme_path in dir_path.glob('**/README.md'):
    if '.terraform' in str(readme_path):
      continue
    diff = None
    readme = readme_path.read_text()
    mod_name = str(readme_path.relative_to(dir_path).parent)
    result = tfdoc.get_doc(readme)
    if not result:
      state = State.SKIP
    else:
      try:
        new_doc = tfdoc.create_doc(
            readme_path.parent, files=files, show_extra=show_extra)
      except SystemExit:
        state = state.SKIP
      else:
        if new_doc == result['doc']:
          state = State.OK
        else:
          state = State.FAIL
          diff = '\n'.join(
              [f'----- {mod_name} diff -----\n'] +
              list(difflib.ndiff(
                  result['doc'].split('\n'), new_doc.split('\n')
              )))
    yield mod_name, state, diff


@click.command()
@click.argument('dirs', type=str, nargs=-1)
@ click.option('--files/--no-files', default=False)
@ click.option('--show-diffs/--no-show-diffs', default=False)
@ click.option('--show-extra/--no-show-extra', default=False)
def main(dirs, files=False, show_diffs=False, show_extra=False):
  'Cycle through modules and ensure READMEs are up-to-date.'
  errors = []
  state_labels = {State.FAIL: '✗', State.OK: '✓', State.SKIP: '?'}
  for dir_name in dirs:
    print(f'----- {dir_name} -----')
    for mod_name, state, diff in _check_dir(dir_name, files, show_extra):
      if state == State.FAIL:
        errors.append(diff)
      print(f'[{state_labels[state]}] {mod_name}')
  if errors:
    if show_diffs:
      print('\n'.join(errors))
    raise SystemExit('Errors found.')


if __name__ == '__main__':
  main()
