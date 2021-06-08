from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    template_name = 'about/author.html'


class AboutTechView(TemplateView):
    template_name = 'about/tech.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['just_title'] = 'Технологии'
        context['just_tech'] = ('<p>Python</p><p>Django 2.2.19</p>'
                                '<p>Bootstrap</p>')
        context['just_text'] = ('<h3>Проект <span style="color:red">Ya</span>'
                                'TUBE</h3>'
                                '<p>Благодаря этому проекту вы сможете'
                                ' создавать посты и делится своими '
                                'впечатлениями о хорошо проведенном '
                                'времени.</p>'
                                '<p>Свои пожелания, а так же какие-либо '
                                'идеи для развития проекта можете отправить '
                                'мне просмотрев контактные данные во вкладе '
                                '"Об авторе"</p>')
        return context
