# bash completion file for atomicapp commands
#
# This script provides completion of:
#  - commands and their options
#
# To enable the completions either:
#  - place this file in /etc/bash_completion.d
#  or
#  - copy this file to e.g. ~/.atomicapp.sh and add the line
#    below to your .bashrc after bash completion features are loaded
#    . ~/.atomicapp.sh
#


_atomicapp() {

        local cur prev
        COMPREPLY=()
        cur=${COMP_WORDS[COMP_CWORD]}
        prev=${COMP_WORDS[COMP_CWORD-1]}

        case "${prev}" in
         --mode)
                COMPREPLY=( $(compgen -W "fetch run stop genanswers" -- $cur) )
                return 0
                ;;

         --answers-format)
                COMPREPLY=( $(compgen -W "ini json xml yaml" -- $cur) )
                return 0
                ;;

         --providertlsverify)
                COMPREPLY=( $(compgen -W "True False" -- $cur) )
                return 0
                ;;

         --logtype)
                COMPREPLY=( $(compgen -W "cockpit color nocolor none" -- $cur) )
                return 0
                ;;
        esac

        if [[ "$cur" == -* ]]; then
            COMPREPLY=($(compgen -W "-V -v -q" -- $cur))

        fi

        if [[ "$cur" == --* ]]; then
             COMPREPLY=( $(compgen -W "--help --version --verbose --quiet --mode --dry-run --answers-format --namespace --providertlsverify --providerconfig --providercafile --providerapi --logtype" -- $cur) )

        fi

}

complete -F _atomicapp atomicapp
