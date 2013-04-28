from appindicator import Indicator, STATUS_ACTIVE, CATEGORY_SYSTEM_SERVICES
import pygtk
import gtk
from subprocess import check_output, CalledProcessError
import gobject
pygtk.require( '2.0' )

LABEL_GUIDE = '9999 ms'


class PingIndicator():

    def __init__( self ):
        #Setting up the indicator

        self.indicator = Indicator( 'ping-indicator', 'ping-indicator', CATEGORY_SYSTEM_SERVICES, '' )
        self.indicator.set_attention_icon( 'amazonCheck_indicator_attention' )
        self.indicator.set_status( STATUS_ACTIVE )

        menu_item_exit = gtk.MenuItem( 'Exit' )
        menu_item_exit.connect( 'activate', self.exit_application )

        indicator_menu = gtk.Menu()
        indicator_menu.append( menu_item_exit )
        indicator_menu.show_all()

        self.indicator.set_menu( indicator_menu )
        self.indicator.set_property( 'label-guide', LABEL_GUIDE )
        self.indicator.set_label( 'Ping', LABEL_GUIDE )

        gobject.timeout_add( 2000, self.update_indicator )


    def exit_application( self, widget ):
        gtk.main_quit()


    def update_indicator( self ):
        #print self.indicator.get_label_guide()

        try:
            output = check_output( [ "ping", "-c", "1", "-W", "2", "8.8.8.8" ] )

            for line in output.splitlines():
                new_label = "NO-CON"

                if line.find( "time=") != -1:
                    new_label = line[ line.find( "time=") + 5 : -3 ]
                    break

        except CalledProcessError:
            new_label = "offline"

        self.indicator.set_label( new_label, LABEL_GUIDE )

        return True


myIndicator = PingIndicator()

gtk.main()



