/**
 * Created by william on 18/08/16.
 */


function table_setup(){

    var defaults = {
            data: null,
            defaultContent: '',
            className: 'select-checkbox',
            orderable: false
        };

        var select_options = {
            style:    'os',
            selector: 'td:first-child'
        }

        var id_field = 'user_id';
        var ajax_url = '/admin_user_table';
        var fieldnames = [
        { label: 'Password Attempts', name: 'password_try_count'},
        { label: 'Username',  name: 'username'  },
        { label: 'Name',  name: 'name'  },
        { label: 'Access Level',  name: 'access_level'  },
        { label: 'Password',  name: 'password', type: 'password'  }
        ];

        var column_data = [
                    defaults,
        { data: 'password_try_count'},
        { data: 'username' },
        { data: 'name' },
        { data: 'access_level' },
        { data: 'password' }
    ];

        var column_titles = [
        {'title':'Password Attempts', 'targets': 1},
        {'title':'Username', 'targets': 2},
        {'title':'Name', 'targets': 3},
        {'title':'Access Level', 'targets': 4},
        {'title':'Password', 'targets': 5}
        ];

    var editor = new $.fn.dataTable.Editor( {
    ajax:  ajax_url,
    table: '#example',
    idSrc:  id_field,
    fields: fieldnames
    } );

    var table = $('#example').DataTable( {
    ajax: ajax_url,
    destroy: true,
    dom: 'Bfrtip',
    columns: column_data,
    columnDefs: column_titles,
    select: select_options,
    buttons: [
        { extend: 'create', editor: editor },
        { extend: 'edit',   editor: editor },
        { extend: 'remove', editor: editor }
    ]
    } );

    table.buttons().container()
        .insertBefore( '#example_filter' );

    // Activate an inline edit on click of a table cell
    $('#example').on( 'click', 'tbody td:not(:first-child)', function (e) {
        editor.inline( this );
    } );

 }//table_setup