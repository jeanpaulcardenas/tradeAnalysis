from dash import Dash, html, dcc, Input, Output, callback, State
from data_classes.mt4data import TxtParser

app = Dash(__name__)

app.layout = html.Div([dcc.Upload(
    id='upload-data',
    children=[
        html.Div(['Drag and drop or\n',
        html.A('Select file')],
                 style={
                     'width': '100%',
                     'height': '60px',
                     'lineHeight': '60px',
                     'borderWidth': '1px',
                     'borderStyle': 'dashed',
                     'borderRadius': '5px',
                     'textAlign': 'center',
                     'margin': '10px'
                 },
                 )
    ],
    multiple=False),
    html.Div(id='output-data-upload')])


def parse_contents(contents, filename, date):

    content_type, content_string = contents.split(',')

    try:
        if 'txt' in filename:
            statement = TxtParser.from_dash_upload(content_string)
            statement.get_account_info()
            statement.get_operations_info()

    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    return html.Div([
        html.H5(filename),

        # dash_table.DataTable(
        #     df.to_dict('records'),
        #     [{'name': i, 'id': i} for i in df.columns]
        # ),

        html.Hr(),  # horizontal line

        # For debugging, display the raw contents provided by the web browser
        html.Div('Raw Content'),
        html.Pre(contents[0:200] + '...', style={
            'whiteSpace': 'pre-wrap',
            'wordBreak': 'break-all'
        })
    ])

@callback(Output('output-data-upload', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(list_of_contents, list_of_names, list_of_dates)]
        return children






if __name__ == '__main__':
    app.run(debug=True)
