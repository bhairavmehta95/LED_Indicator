from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()

#import hello.views
import tutorial.views

# Examples:
# url(r'^$', 'gettingstarted.views.home', name='home'),
# url(r'^blog/', include('blog.urls')),

urlpatterns = [
    url(r'^$', 'tutorial.views.home', name='home'),
    # Defer any URLS to the /tutorial directory to the tutorial app
    url(r'^tutorial/', include('tutorial.urls', namespace='tutorial')),
    url(r'^admin/', include(admin.site.urls)),
]
