#!/usr/bin/python2.7 -u

from appindicator import Indicator, STATUS_ACTIVE, CATEGORY_SYSTEM_SERVICES
from subprocess import check_output, CalledProcessError
from gobject import timeout_add
from time import strftime
from gtk import Menu, MenuItem, SeparatorMenuItem, main, main_quit

class PingIndicator():

    def __init__( self ):
        self.LABEL_GUIDE = '9999'
        self.online = True

        self.indicator = Indicator( 'ping-indicator', 'ping-indicator', CATEGORY_SYSTEM_SERVICES, '' )
        self.indicator.set_status( STATUS_ACTIVE )

        menu_item_since = MenuItem( 'Online since: ' + strftime( '%H:%M:%S' ) )
        menu_separator  = SeparatorMenuItem()
        menu_item_exit =  MenuItem( 'Exit' )
        menu_item_exit.connect( 'activate', self.stop )

        indicator_menu = Menu()
        indicator_menu.append( menu_item_since )
        indicator_menu.append( menu_separator  )
        indicator_menu.append( menu_item_exit  )
        indicator_menu.show_all()

        self.indicator.set_menu( indicator_menu )
        self.indicator.set_label( 'Ping', self.LABEL_GUIDE )

        timeout_add( 2000, self.update_indicator )


    def stop( self, widget=None ):
        main_quit()


    def update_indicator( self ):

        new_label = "offline"

        try:
            output = check_output( [ "ping", "-c", "1", "-W", "2", "8.8.8.8" ] )

            for line in output.splitlines():
                if line.find( "time=") != -1:
                    new_label = line[ line.find( "time=") + 5 : -3 ].center( 4 )

                    if not self.online:
                        self.online = True
                        self.indicator.get_menu().get_children()[0].set_label( 'Last disconnect: ' + strftime( '%H:%M:%S' ) )

                    break
        except CalledProcessError:
            if self.online:
                self.online = False
                self.indicator.get_menu().get_children()[0].set_label( 'Offline since: ' + strftime( '%H:%M:%S' ) )

        self.indicator.set_label( new_label, self.LABEL_GUIDE )
        return True


    def run( self ):
        main()

if __name__ == '__main__':
    PingIndicator().run()



