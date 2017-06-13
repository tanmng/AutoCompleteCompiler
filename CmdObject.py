'''Classes of objects that we use to construct the command tree for autocompletion library
'''
import subprocess
import os
import re
class CmdObject(object):
    '''Representation of an arbitrary command/subcommand as a node in a tree
    '''

    '''When this object is a command/subcommand'''
    TYPE_COMMAND = 1
    '''When this object is a option/switch'''
    TYPE_OPTION = 2

    def __init__(self, cmd, type, desc, path, binary, arguments):
        '''Initialize
        '''
        self.cmd = cmd
        self.type = type
        self.desc = desc
        self.path = path
        self.binary = binary
        self.arguments = arguments
        self.expanded = False

    def get_output(self, *arbitrary_args):
        '''Retrieve output when execute our command/subcommand with arguments'
        '''
        cmd = [os.path.join(self.path, self.binary)] + list(self.arguments) + list(arbitrary_args)
        # print cmd
        # In case our binary returns non-zero exit code
        # for some help commands so can't use subprocess.check_output here
        ps = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, _ = ps.communicate()
        out = out.decode('utf-8')
        return iter(out.splitlines())

    def get_condition(self):
        '''Return the Fish function to confirm that this is running
        '''
        # Implement this you twat
        if self.type != self.TYPE_COMMAND:
            return ''

        # Process
        result = ''
        result += 'function ' + self.get_condition_function_name() + '\n'
        result += '  if [ !(__fish_terraform_command_count {len})'.format(
            len=len(self.arguments) + 1
        )
        result += (' -o ' if (len(self.arguments) > 1) else '')
        result += ' -o '.join(['!(__fish_terraform_using_command {arg} {index})'.format(
            arg=arg,
            index=index + 2
        ) for index, arg in enumerate(self.arguments[:-1])])
        result += ' ]\n'
        result += '    return 1\n'
        result += '  end\n'
        result += '  return 0\n'
        result += 'end'
        return result

    def get_completion(self):
        '''Return completion
        '''
        result = ''
        if self.type == self.TYPE_COMMAND:
            result = 'complete -c {command} -n "{condition}" -f -a {cmd} -d \'{desc}\''.format(
                command=self.binary,
                desc=self.desc,
                cmd=self.cmd,
                condition=self.get_condition_function_name(),
            )
        return result

    def has_condition(self):
        '''Notify whether this is a command and thus can us a condition function
        '''
        # Implement this you twat
        return self.type == self.TYPE_COMMAND

    def get_condition_function_name(self):
        '''Generate a name for a subcommand condition'
        '''
        return '__fish_{binary}_can_use_{arg_list}'.format(
            binary=self.binary,
            arg_list=('_'.join(self.arguments) if len(self.arguments) > 0 else 'BARE')
        )

    def get_identifier(self):
        '''Return a uniquue string to represent this object in our tree as its ID
        '''
        identifier_parts = self.arguments + [self.cmd]
        return '.'.join(identifier_parts)

    def get_tag(self):
        '''Return a string to represent this object in our tree view
        '''
        # return ('C+' if self.type == self.TYPE_COMMAND else 'O+') + self.cmd
        return self.cmd

    def is_expandable(self):
        '''Return whether we can still expand this node
        '''
        return (self.type == self.TYPE_COMMAND and not self.expanded)

    def mark_expanded(self, val = True):
        '''Makr wherether this object is expanded for subcommand/options
        '''
        self.expanded = val

