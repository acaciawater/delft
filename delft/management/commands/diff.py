from django.core.management.base import BaseCommand
from acacia.data.models import Series, ManualSeries
import pandas as pd
from acacia.meetnet.models import Screen

class Command(BaseCommand):
    args = ''
    help = 'Vergelijk standen en handpeilingen'

    def handle(self, *args, **options):

        tolerance = pd.Timedelta('1 hour')
        print 'tolerance:',tolerance
        
        header = True
        with open('diff.csv','w') as csv:
            for screen in Screen.objects.all():
                print unicode(screen),
                hand = screen.get_manual_series()
                if hand is None:
                    print 'geen handpeilingen'
                else:
                    src = screen.get_compensated_series()
                    if src is None:
                        print 'geen loggerdata'
                    else:
                        try:
                            data = src.reindex(hand.index,method='nearest',tolerance=tolerance)
                            verschil = data - hand
                            df = pd.DataFrame({'filter': unicode(screen), 'data': data, 'hand': hand, 'verschil': verschil})
                            df.dropna(inplace=True)
                            print verschil.mean()
                            df.to_csv(csv,header=header)
                            header = False
                        except Exception as e:
                            print 'problem with',screen,e

            