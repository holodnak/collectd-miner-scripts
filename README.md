collectd miner metric gathering scripts

(c) 2018 holodnak

All of the scripts use some custom data types, make sure to add it to your configuration file you create in /etc/collectd/collectd.conf.d/ directory.

Example:

  TypesDB "/home/james/bin/types.db.custom"


To use the plugin, add lines similar to the lines below to your configuration file.

All plugins have the same configuration options.  Declare multiple instances for the plugin to monitor multiple miners.

<Plugin python>
        ModulePath "/home/james/bin"
        LogTraces true
        Import "claymore"
        <Module claymore>
                interval "10"
                <Instance miner>
                        url "http://192.168.50.161:3333/"
                        rigname "winminer2"
                </Instance>
        </Module>
</Plugin>


** beta software, contains virus-stealing malware **

