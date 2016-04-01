# atomicapp_cli_completion
# bash completion file for atomicapp commands
# To enable the completions
# copy this file to  ~/.bash_completion.d/
# . ~/.bash_completion.d/atomicapp


_atomicapp() {


        local cur=${COMP_WORDS[COMP_CWORD]}
        local prev=${COMP_WORDS[COMP_CWORD-1]}

        case "$prev" in
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
             COMPREPLY=( $(compgen -W "--version --verbose --quiet --mode --dry-run --answers-format --namespace --providertlsverify --providerconfig --providercafile --providerapi --logtype" -- $cur) )

        fi


}

complete -F _atomicapp atomicapp

