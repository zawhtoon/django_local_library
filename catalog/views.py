from django.shortcuts import get_object_or_404, render
from django.http import Http404
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

import datetime
from .models import Book, Author, BookInstance, Genre, Language
from .forms import RenewBookForm, RenewBookModelForm

from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy


# Create your views here.

@login_required
def index(request):
    """
    View function for home page of site.
    """
    # Generate counts of some of the main objects
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    # Available catalog (status = 'a')
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()
    num_authors = Author.objects.count()  # The 'all()' is implied by default.

    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    # Render the HTML template index.html with the data in the context variable
    return render(
        request,
        'index.html',
        context={'num_books': num_books, 'num_instances': num_instances,
                 'num_instances_available': num_instances_available, 'num_authors': num_authors,
                 'num_visits': num_visits},  # num_visits appended
    )


class BookListView(LoginRequiredMixin, generic.ListView):
    model = Book
    paginate_by = 2
    # context_object_name = 'my_book_list'  # your own name for the list as a template variable
    # queryset = Book.objects.filter(title__icontains='war')[:5]  # Get 5 catalog containing the title war
    # template_name = 'catalog/book_list.html'  # Specify your own template name/location

    def get_queryset(self):
        return Book.objects.all() #filter(title__icontains='war')[:5]  # Get 5 catalog containing the title war

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(BookListView, self).get_context_data(**kwargs)
        # Get the blog from id and add it to the context
        context['some_data'] = 'This is just some data'
        return context


class BookDetailView(LoginRequiredMixin, generic.DetailView):
    model = Book

@login_required
def book_detail_view(request, pk):
    try:
        book_id = Book.objects.get(pk=pk)
    except Book.DoesNotExist:
        raise Http404("Book does not exist")

    # book_id=get_object_or_404(Book, pk=pk)

    return render(
        request,
        'catalog/book_detail.html',
        context={'book': book_id, }
    )


class AuthorListView(LoginRequiredMixin, generic.ListView):
    model = Author
    paginate_by = 10

    def get_queryset(self):
        return Author.objects.all()


class AuthorDetailView(LoginRequiredMixin, generic.DetailView):
    model = Author

@login_required
def author_detail_view(request, pk):
    author_id = get_object_or_404(Author, pk)

    return render(
        request,
        'catalog/author_detail.html',
        context={'author': author_id, }
    )


class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """
    Generic class-based view listing books on loan to current user.
    """
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')

class LoanedBooksView(PermissionRequiredMixin, generic.ListView):
    permission_required = 'catalog.can_mark_returned'
    # Or multiple permissions
    #permission_required = ('catalog.can_mark_returned', 'catalog.can_edit')
    # Note that 'catalog.can_edit' is just an example
    # the catalog application doesn't have such permission!
    model = BookInstance
    template_name = 'catalog/borrowed.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')

@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
    """
    View function for renewing a specific BookInstance by librarian
    """
    book_inst=get_object_or_404(BookInstance, pk = pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewBookModelForm(request.POST) #RenewBookForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            # book_inst.due_back = form.cleaned_data['renewal_date']
            book_inst.due_back = form.cleaned_data['due_back']
            book_inst.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('all-borrowed') )

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        # form = RenewBookForm(initial={'renewal_date': proposed_renewal_date,})
        form = RenewBookModelForm(initial={'renewal_date': proposed_renewal_date, })

    return render(request, 'catalog/book_renew_librarian.html', {'form': form, 'bookinst':book_inst})


class AuthorCreate(CreateView):
    model = Author
    fields = '__all__'
    initial={'date_of_death':'12/10/2016',}


class AuthorUpdate(UpdateView):
    model = Author
    fields = ['first_name','last_name','date_of_birth','date_of_death']


class AuthorDelete(DeleteView):
    model = Author
    success_url = reverse_lazy('authors')


class BookCreate(CreateView):
    model = Book
    fields = '__all__'


class BookUpdate(UpdateView):
    model = Book
    fields = ['title', 'author', 'summary', 'isbn', 'genre', 'language']


class BookDelete(DeleteView):
    model = Book
    success_url = reverse_lazy('books')



