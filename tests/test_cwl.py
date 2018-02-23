# -*- coding: utf-8 -*-
#
# Copyright 2018 - Swiss Data Science Center (SDSC)
# A partnership between École Polytechnique Fédérale de Lausanne (EPFL) and
# Eidgenössische Technische Hochschule Zürich (ETHZ).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from renga._compat import Path
from renga.models.cwl.command_line_tool import CommandLineTool, \
    CommandLineToolFactory


def test_1st_tool():
    """Check creation of 1st tool example from args."""
    tool = CommandLineToolFactory(('echo', 'Hello world!')).generate_tool()
    assert tool.cwlVersion == 'v1.0'
    assert tool.__class__.__name__ == 'CommandLineTool'
    assert tool.inputs[0].default == 'Hello world!'


def test_03_input(instance_path):
    """Check the essential input parameters."""
    whale = Path(instance_path) / 'whale.txt'
    whale.touch()

    tool = CommandLineToolFactory((
        'echo',
        '-f',
        '-i42',
        '--example-string',
        'hello',
        '--file=whale.txt',
    ), directory=instance_path).generate_tool()

    assert tool.arguments[0].prefix == '-f'

    assert tool.inputs[0].default == 42
    assert tool.inputs[0].type == 'int'
    assert tool.inputs[0].inputBinding.prefix == '-i'
    assert tool.inputs[0].inputBinding.separate is False

    assert tool.inputs[1].default == 'hello'
    assert tool.inputs[1].type == 'string'
    assert tool.inputs[1].inputBinding.prefix == '--example-string'
    assert tool.inputs[1].inputBinding.separate is True

    assert tool.inputs[2].default.path == Path('whale.txt')
    assert tool.inputs[2].type == 'File'
    assert tool.inputs[2].inputBinding.prefix == '--file='
    assert tool.inputs[2].inputBinding.separate is False


def test_base_command_detection(instance_path):
    """Test base command detection."""
    hello = Path(instance_path) / 'hello.tar'
    hello.touch()

    tool = CommandLineToolFactory(('tar', 'xf', 'hello.tar'),
                                  directory=instance_path).generate_tool()

    assert tool.baseCommand == ['tar', 'xf']
    assert tool.inputs[0].default.path == Path('hello.tar')
    assert tool.inputs[0].type == 'File'
    assert tool.inputs[0].inputBinding.prefix is None
    assert tool.inputs[0].inputBinding.separate is True


def test_short_base_command_detection():
    """Test base command detection without arguments."""
    tool = CommandLineToolFactory(('echo', 'A')).generate_tool()
    assert tool.cwlVersion == 'v1.0'
    assert tool.__class__.__name__ == 'CommandLineTool'
    assert tool.inputs[0].default == 'A'


def test_04_output(instance_path):
    """Test describtion of outputs from a command."""
    hello = Path(instance_path) / 'hello.tar'
    hello.touch()

    factory = CommandLineToolFactory(('tar', 'xf', 'hello.tar'),
                                     directory=instance_path)

    # simulate run

    output = Path(instance_path) / 'hello.txt'
    output.touch()

    parameters = list(factory.guess_outputs([output]))

    assert parameters[0][0].type == 'File'
    assert parameters[0][0].outputBinding.glob == 'hello.txt'


def test_05_stdout(instance_path):
    """Test stdout mapping."""
    output = Path(instance_path) / 'output.txt'
    output.touch()

    factory = CommandLineToolFactory(
        ('echo', 'Hello world!'),
        directory=instance_path,
        stdout='output.txt',
    )

    assert factory.stdout == 'output.txt'
    assert factory.outputs[0].type == 'stdout'


def test_06_params(instance_path):
    """Test referencing input parameters in other fields."""
    hello = Path(instance_path) / 'hello.tar'
    hello.touch()

    factory = CommandLineToolFactory(
        ('tar', 'xf', 'hello.tar', 'goodbye.txt'),
        directory=instance_path,
    )

    assert factory.inputs[1].default == 'goodbye.txt'
    assert factory.inputs[1].type == 'string'
    assert factory.inputs[1].inputBinding.position == 2

    goodbye_id = factory.inputs[1].id

    # simulate run

    output = Path(instance_path) / 'goodbye.txt'
    output.touch()

    parameters = list(factory.guess_outputs([output]))

    assert parameters[0][0].type == 'File'
    assert parameters[0][0].outputBinding.glob == \
        '$(inputs.{0})'.format(goodbye_id)


def test_09_array_inputs(instance_path):
    """Test specification of input parameters in arrays."""
    tool = CommandLineToolFactory(
        ('echo',
         '-A', 'one', 'two', 'three',
         '-B=four', '-B=five', '-B=six',
         '-C=seven,eight,nine', ), directory=instance_path).generate_tool()

    # TODO add grouping for -A and -B

    assert tool.inputs[-1].type == 'string[]'
    assert tool.inputs[-1].default == ['seven', 'eight', 'nine']
    assert tool.inputs[-1].inputBinding.prefix == '-C='
    assert tool.inputs[-1].inputBinding.itemSeparator == ','
    assert tool.inputs[-1].inputBinding.separate is False