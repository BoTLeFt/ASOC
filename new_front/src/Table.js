import React, { useState, useEffect } from "react";
import { DataTable } from "primereact/datatable";
import { Column } from "primereact/column";
import { MultiSelect } from "primereact/multiselect";
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { SelectButton } from 'primereact/selectbutton';
import Dashboard from "./Dashboard";
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Tag } from 'primereact/tag';


const Table = () => {
  const [selectedProduct, setSelectedProduct] = useState(null);

  // Проверяем, есть ли токен в localStorage
  var token = localStorage.getItem('access_token');
  if (!token) {
    alert('Токен не найден. Перенаправляем на страницу аутентификации.');
    window.location.href = '/login'; // Перенаправляем на страницу аутентификации
  }
  const [data, setData] = useState(null);

  const statusChangeBodyTemplate = (rowData) => {
    const handleChange = (e) => {
      const newStatus = e.value;
      const updatedData = [...data];
      const rowIndex = updatedData.findIndex(item => item.id === rowData.id);
      updatedData[rowIndex].status = newStatus;
      setData(updatedData);
  
      const requestOptions = {
        method: 'POST',
        headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
        body: JSON.stringify({ matchBasedId: updatedData[rowIndex].matchbasedid, status:  updatedData[rowIndex].status})
      };
      fetch('http://host.docker.internal:8080/change_status', requestOptions)
      .then(response => {
        console.log('Status updated successfully:', updatedData[rowIndex].status);
      })
      .catch(error => {
        console.error('Error updating status:', error);
      });

      Dashboard.forceUpdate()
    };
  
    return (
      <SelectButton
        value={rowData.status}
        options={statusSelectItems}
        onChange={handleChange}
      />
    );
  };

  const codeBodyTemplate = (rowData) => {
    return(<SyntaxHighlighter language="csharp">
      {rowData.code_line}
    </SyntaxHighlighter>)
  };

  const messageBodyTemplate = (rowData) => {
    return(<Markdown remarkPlugins={[remarkGfm]}>{rowData.message}</Markdown>)
  };

  const severityBodyTemplate = (rowData) => {
    if (rowData.severity == "Critical") {
      return(<Tag severity="danger" value={rowData.severity}></Tag>)
    } else if (rowData.severity == "Medium") {
      return(<Tag severity="warning" value={rowData.severity}></Tag>)
    } else if (rowData.severity == "Low") {
      return(<Tag severity="info" value={rowData.severity}></Tag>)
    } else {
      return(<Tag severity="secondary" value={rowData.severity}></Tag>)
    }
  };

  const authorBodyTemplate = (rowData) => {
    return(<div>{rowData.author.split("+")[0]}</div>)
  };
  
  const urlBodyTemplate = (rowData) => {
    return(<a href={rowData.uri_line}>{rowData.uri_line}</a>)
  };


  const defaultColumns = [
    { field: "severity", header: "Критичность", template: severityBodyTemplate },
    { field: "short_desc", header: "Short description" },
    { field: "status", header: "Изменить статус", template: statusChangeBodyTemplate }
  ];

  const columns = [
    { field: "severity", header: "Критичность", template: severityBodyTemplate },
    { field: "short_desc", header: "Короткое описание" },
    { field: "project", header: "Имя репозитория" },
    { field: "author", header: "Автор", template: authorBodyTemplate },
    { field: "code_line", header: "Код сработки", template: codeBodyTemplate },
    { field: "message", header: "Описание", template: messageBodyTemplate },
    { field: "uri_line", header: "URL до сработки", template: urlBodyTemplate },
    { field: "commit_hash", header: "Хэш коммита" },
    { field: "ruleid", header: "ID правила" },
    { field: "matchbasedid", header: "ID сработки" },
    { field: "notification_status", header: "Статус нотификации" },
    { field: "status", header: "Изменить статус", template: statusChangeBodyTemplate }
  ];

  const [visibleColumns, setVisibleColumns] = useState(defaultColumns);

  const statusSelectItems = [
    {label: 'Created', value: 'created'},
    {label: 'False Positive', value: 'False Positive'},
    {label: 'True Positive', value: 'True Positive'},
    {label: 'Need review', value: 'Need review'},
    {label: 'Fixed', value: 'Fixed'}
  ];

  useEffect(() => {
    fetch("http://host.docker.internal:8080/data", {
      method: "GET",
      headers: {
        'Authorization': 'Bearer ' + token,
      },
    })
      .then(response => response.json())
      .then((usefulData) => {
        console.log(usefulData);
        setData(usefulData);
      })
      .catch((e) => {
        console.error(`An error occurred: ${e}`)
      });
  }, []);

  const onColumnToggle = (event) => {
    let selectedColumns = event.value;
    let orderedSelectedColumns = columns.filter((col) =>
      selectedColumns.some((sCol) => sCol.field === col.field)
    );

    setVisibleColumns(orderedSelectedColumns);
  };
  const header = (
    <MultiSelect
      value={visibleColumns}
      options={columns}
      optionLabel="header"
      onChange={onColumnToggle}
      className="w-full sm:w-20rem"
      display="chip"
    />
  );
  const footer = <p>Total data = {data ? data.length : 0}</p>;

  

  return (
    <div className="table-wrapper">
      <h2 className="table-name">PrimeReact data table</h2>
      <DataTable
        value={data}
        responsiveLayout="scroll"
        size="normal"
        showGridlines
        stripedRows
        header={header}
        footer={footer}
        removableSort
        paginator
        paginatorTemplate="CurrentPageReport FirstPageLink PrevPageLink PageLinks
      NextPageLink LastPageLink"
        rows={5}
        selection={selectedProduct}
        onSelectionChange={(e) => setSelectedProduct(e.value)}
        dataKey="id"
        >
        {visibleColumns.map(col => {
          if (col.template) {
            return (
              <Column
                key={col.field}
                field={col.field}
                header={col.header}
                body={col.template}
                filter
                sortable
              />
            )
          } else {
            return (
              <Column
                key={col.field}
                field={col.field}
                header={col.header}
                filter
                sortable
              />
            )
          }
        }
        )}
      </DataTable>
    </div>
  );
};

export default Table;