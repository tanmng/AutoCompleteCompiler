#!/usr/bin/env python
from CmdObject import *
import copy
from treelib import Tree, Node

cmd_obj = CmdObject(
    cmd='terraform',
    type=CmdObject.TYPE_COMMAND,
    desc='terraform',
    path='/Users/dra/bin',
    binary='terraform',
    arguments=[],
)

new_node = Node(
    identifier=cmd_obj.get_identifier(),
    tag=cmd_obj.get_tag(),
)
new_node.data = cmd_obj

tftree = Tree()

tftree.add_node(new_node)
#print tftree

command_listing_beginning = re.compile('^.*commands\:$')
command_listing_detail_line = re.compile('[a-z]+  +[A-Z].*$')
option_listing_beginning = re.compile('^Options:$')
option_listing_detail_line_with_name = re.compile('-[a-z -0-9=]+  +[A-Z].*$')



counter = 0
while True:
    counter += 1
    all_leaves = tftree.leaves()
    no_leaf_expandable = True
    for leaf in all_leaves:
        leaf_data = leaf.data
        if leaf_data.is_expandable():
            # Mark this value so that we do not escape from exploring
            no_leaf_expandable = False

            # Get the help value of this
            output = leaf_data.get_output('-help')

            command_listing = []
            command_listing_mode = False
            option_listing = []
            option_listing_mode = False
            current_option = None

            for line in output:
                line = line.strip()
                if command_listing_beginning.match(line):
                    # We will now start processing subcommands
                    command_listing_mode = True
                if option_listing_beginning.match(line):
                    # We will now start processing subcommands
                    option_listing_mode = True
                    continue
                if command_listing_mode:
                    # We are processing command listing
                    if command_listing_detail_line.match(line):
                        # Break this down to command and description
                        parts = re.compile('  +').split(line)
                        command = parts[0]
                        desc = parts[1]
                        command_listing.append({
                            'cmd': command,
                            'desc': desc,
                        })
                elif option_listing_mode:
                    # We are processing option listing
                    # print line
                    if len(line) == 0:
                        # This is the divider between different options
                        if current_option is not None:
                            # We are indeed processing some option
                            option_listing.append(current_option)
                            current_option = None
                    else:
                        # It's a line with our options
                        if current_option is None or option_listing_detail_line_with_name.match(line):
                            # It's the first line of the option listing which include the name
                            parts = re.compile(' +').split(line)
                            option = parts[0]
                            option_cleaned = re.compile('^[^=]+').search(option).group(0)
                            desc = parts[1]
                            current_option = {
                                'opt': option_cleaned,
                                'desc': desc,
                            }
                        else:
                            # This is the following line of an option, we extract the description from it
                            current_option['desc'] += line


                # print line
            # Add the children of our current node
            # print command_listing
            for subcommand in command_listing:
                cmd_obj = CmdObject(
                    cmd=subcommand['cmd'],
                    type=CmdObject.TYPE_COMMAND,
                    desc=subcommand['desc'],
                    path=leaf_data.path,
                    binary=leaf_data.binary,
                    arguments=copy.deepcopy(leaf_data.arguments) + [subcommand['cmd']]
                )
                new_node = Node(
                    identifier=cmd_obj.get_identifier(),
                    tag=cmd_obj.get_tag()
                )
                new_node.data = cmd_obj
                tftree.add_node(
                    node=new_node,
                    parent=leaf.identifier,
                )

            # Add the default help option for any command we can find
            option_listing.append({
                'opt': '-help',
                'desc': 'Get help about this command'
            })
            for option in option_listing:
                cmd_obj = CmdObject(
                    cmd=option['opt'],
                    type=CmdObject.TYPE_OPTION,
                    desc=option['desc'],
                    path=leaf_data.path,
                    binary=leaf_data.binary,
                    arguments=copy.deepcopy(leaf_data.arguments) + [option['opt']]
                )
                new_node = Node(
                    identifier=cmd_obj.get_identifier(),
                    tag=cmd_obj.get_tag()
                )
                new_node.data = cmd_obj
                tftree.add_node(
                    node=new_node,
                    parent=leaf.identifier,
                )
            leaf_data.mark_expanded()


    # print tftree

    if no_leaf_expandable or counter == 2:
        break

print '''
# Terraform autocompletion for Fish shell
# Credit to Manh Tan Nguyen <tan.mng90@gmail.com>

# Helper function to get current command with terraform
function __fish_terraform_get_cmd
  for c in (commandline -opc)
    if not string match -q -- '-*' $c
      echo $c
    end
  end
end


function __fish_terraform_using_command
  set index 2

  if set -q argv[2]
    set index $argv[2]
  end

  set cmd (__fish_terraform_get_cmd)

  if set -q cmd[$index]
    if [ $argv[1] = $cmd[$index] ]
      return 0
    end
  end
  return 1
end


function __fish_terraform_command_count
  set cmd (__fish_terraform_get_cmd)
  set cmd_count (count $cmd)

  if [ $cmd_count = $argv[1] ]
    return 0
  end
  return 1
end

'''

for node_id in tftree.expand_tree(
    nid=tftree.root,
    mode=Tree.WIDTH,
):
    node = tftree.get_node(node_id)
    node_data = node.data
    if node_data.has_condition():
        print node_data.get_condition()

for node_id in tftree.expand_tree(
    nid=tftree.root,
    mode=Tree.WIDTH,
):
    node = tftree.get_node(node_id)
    node_data = node.data
    print node_data.get_completion()

